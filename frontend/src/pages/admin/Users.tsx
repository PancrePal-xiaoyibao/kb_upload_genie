import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Input,
  Select,
  Space,
  Tag,
  Avatar,
  Modal,
  message,
  Popconfirm,
  Typography,
  Descriptions,
  Spin,
  Row,
  Col,
} from 'antd';
import {
  ReloadOutlined,
  UserOutlined,
  EditOutlined,
  StopOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { getAllUsers, getUserDetail, updateUserStatus, UserStatus } from '@/services/admin';
import type { UserInfo } from '@/services/auth';
import dayjs from 'dayjs';
import './Users.css';

const { Search } = Input;
const { Option } = Select;
const { Title, Text } = Typography;

const Users: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<UserInfo[]>([]);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedUser, setSelectedUser] = useState<UserInfo | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const data = await getAllUsers();
      setUsers(data);
      setFilteredUsers(data);
    } catch (error: any) {
      console.error('获取用户列表失败:', error);
      message.error(error.response?.data?.detail || '获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 过滤用户列表
  const filterUsers = () => {
    let filtered = users;

    // 按搜索文本过滤
    if (searchText) {
      filtered = filtered.filter(user =>
        user.name?.toLowerCase().includes(searchText.toLowerCase()) ||
        user.email.toLowerCase().includes(searchText.toLowerCase())
      );
    }

    // 按状态过滤
    if (statusFilter !== 'all') {
      filtered = filtered.filter(user => user.status === statusFilter);
    }

    setFilteredUsers(filtered);
  };

  // 获取用户详情
  const fetchUserDetail = async (userId: string) => {
    try {
      setDetailLoading(true);
      const data = await getUserDetail(userId);
      setSelectedUser(data);
    } catch (error: any) {
      console.error('获取用户详情失败:', error);
      message.error(error.response?.data?.detail || '获取用户详情失败');
    } finally {
      setDetailLoading(false);
    }
  };

  // 修改用户状态
  const handleUpdateUserStatus = async (userId: string, newStatus: UserStatus) => {
    try {
      await updateUserStatus(userId, newStatus);
      message.success('用户状态修改成功');
      fetchUsers(); // 刷新列表
    } catch (error: any) {
      console.error('修改用户状态失败:', error);
      message.error(error.response?.data?.detail || '修改用户状态失败');
    }
  };

  // 显示用户详情
  const showUserDetail = (user: UserInfo) => {
    setSelectedUser(user);
    setDetailModalVisible(true);
    fetchUserDetail(user.id);
  };

  // 获取状态标签
  const getStatusTag = (status: string) => {
    const statusConfig = {
      active: { color: 'green', text: '活跃' },
      inactive: { color: 'orange', text: '未激活' },
      suspended: { color: 'red', text: '已暂停' },
    };
    
    const config = statusConfig[status as keyof typeof statusConfig] || { color: 'default', text: status };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 获取角色标签
  const getRoleTag = (role: string) => {
    const roleConfig = {
      admin: { color: 'gold', text: '管理员' },
      moderator: { color: 'purple', text: '审核员' },
      user: { color: 'blue', text: '普通用户' },
    };
    
    const config = roleConfig[role as keyof typeof roleConfig] || { color: 'default', text: role };
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 表格列配置
  const columns = [
    {
      title: '用户',
      dataIndex: 'user',
      key: 'user',
      render: (_: any, record: UserInfo) => (
        <Space>
          <Avatar
            size="small"
            icon={<UserOutlined />}
            style={{ backgroundColor: '#1890ff' }}
          />
          <div>
            <div style={{ fontWeight: 500 }}>{record.name || '未设置'}</div>
            <div style={{ fontSize: '12px', color: '#8c8c8c' }}>{record.email}</div>
          </div>
        </Space>
      ),
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => getRoleTag(role),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '注册时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '最后登录',
      dataIndex: 'last_login_at',
      key: 'last_login_at',
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : '从未登录',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: UserInfo) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => showUserDetail(record)}
          >
            详情
          </Button>
          
          {record.status === 'active' ? (
            <Popconfirm
              title="确定要暂停此用户吗？"
              onConfirm={() => handleUpdateUserStatus(record.id, UserStatus.SUSPENDED)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="link"
                size="small"
                danger
                icon={<StopOutlined />}
              >
                暂停
              </Button>
            </Popconfirm>
          ) : (
            <Popconfirm
              title="确定要激活此用户吗？"
              onConfirm={() => handleUpdateUserStatus(record.id, UserStatus.ACTIVE)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="link"
                size="small"
                icon={<CheckCircleOutlined />}
              >
                激活
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    filterUsers();
  }, [searchText, statusFilter, users]);

  return (
    <div className="users-container">
      <Card bordered={false}>
        <div className="users-header">
          <Title level={4} style={{ margin: 0 }}>
            用户管理
          </Title>
          <Text type="secondary">
            管理系统中的所有用户账户
          </Text>
        </div>

        {/* 搜索和过滤工具栏 */}
        <div className="users-toolbar">
          <Row gutter={16} align="middle">
            <Col flex="auto">
              <Space>
                <Search
                  placeholder="搜索用户名或邮箱"
                  allowClear
                  style={{ width: 300 }}
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  onSearch={filterUsers}
                />
                
                <Select
                  value={statusFilter}
                  onChange={setStatusFilter}
                  style={{ width: 120 }}
                >
                  <Option value="all">全部状态</Option>
                  <Option value="active">活跃</Option>
                  <Option value="inactive">未激活</Option>
                  <Option value="suspended">已暂停</Option>
                </Select>
              </Space>
            </Col>
            
            <Col>
              <Button
                icon={<ReloadOutlined />}
                onClick={fetchUsers}
                loading={loading}
              >
                刷新
              </Button>
            </Col>
          </Row>
        </div>

        {/* 用户列表表格 */}
        <Table
          columns={columns}
          dataSource={filteredUsers}
          rowKey="id"
          loading={loading}
          pagination={{
            total: filteredUsers.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          className="users-table"
        />
      </Card>

      {/* 用户详情弹窗 */}
      <Modal
        title="用户详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={600}
        className="user-detail-modal"
      >
        {selectedUser && (
          <div className="user-detail-content">
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <div className="user-detail-header">
                  <Avatar
                    size={64}
                    icon={<UserOutlined />}
                    style={{ backgroundColor: '#1890ff' }}
                  />
                  <div className="user-detail-info">
                    <Title level={4} style={{ margin: 0 }}>
                      {selectedUser.name || '未设置姓名'}
                    </Title>
                    <Text type="secondary">{selectedUser.email}</Text>
                    <div style={{ marginTop: 8 }}>
                      {getRoleTag(selectedUser.role)}
                      {getStatusTag(selectedUser.status)}
                    </div>
                  </div>
                </div>
              </Col>
              
              <Col span={24}>
                {detailLoading ? (
                  <div style={{ textAlign: 'center', padding: '20px' }}>
                    <Spin size="large" />
                  </div>
                ) : (
                  <Descriptions
                    title="基本信息"
                    bordered
                    column={1}
                  >
                    <Descriptions.Item label="用户ID">
                      {selectedUser.id}
                    </Descriptions.Item>
                  <Descriptions.Item label="邮箱地址">
                    {selectedUser.email}
                  </Descriptions.Item>
                  <Descriptions.Item label="用户名">
                    {selectedUser.name || '未设置'}
                  </Descriptions.Item>
                  <Descriptions.Item label="用户角色">
                    {getRoleTag(selectedUser.role)}
                  </Descriptions.Item>
                  <Descriptions.Item label="账户状态">
                    {getStatusTag(selectedUser.status)}
                  </Descriptions.Item>
                  <Descriptions.Item label="注册时间">
                    {dayjs(selectedUser.created_at).format('YYYY-MM-DD HH:mm:ss')}
                  </Descriptions.Item>
                  <Descriptions.Item label="最后登录">
                    {selectedUser.last_login_at 
                      ? dayjs(selectedUser.last_login_at).format('YYYY-MM-DD HH:mm:ss')
                      : '从未登录'
                    }
                  </Descriptions.Item>
                </Descriptions>
                )}
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Users;