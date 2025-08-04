"""
邮件相关的CLI命令
"""

import asyncio
import click
import logging
from datetime import datetime

from app.core.config import settings
from app.services.email_service import email_service
from app.tasks.email_tasks import run_maintenance_tasks, email_task_manager

logger = logging.getLogger(__name__)


@click.group()
def email():
    """邮件相关命令"""
    pass


@email.command()
def check():
    """手动检查邮件"""
    click.echo("开始检查邮件...")
    
    async def _check():
        try:
            await email_task_manager.check_emails_once()
            click.echo("✅ 邮件检查完成")
        except Exception as e:
            click.echo(f"❌ 邮件检查失败: {e}")
    
    asyncio.run(_check())


@email.command()
def maintenance():
    """运行维护任务"""
    click.echo("开始运行维护任务...")
    
    async def _maintenance():
        try:
            await run_maintenance_tasks()
            click.echo("✅ 维护任务完成")
        except Exception as e:
            click.echo(f"❌ 维护任务失败: {e}")
    
    asyncio.run(_maintenance())


@email.command()
@click.option('--email', required=True, help='邮箱地址')
def check_rate_limit(email):
    """检查邮箱的频率限制状态"""
    click.echo(f"检查邮箱 {email} 的频率限制状态...")
    
    async def _check_rate():
        try:
            result = await email_service.check_rate_limit(email)
            click.echo(f"✅ 频率限制检查结果:")
            click.echo(f"   允许发送: {'是' if result['allowed'] else '否'}")
            click.echo(f"   小时内计数: {result['hourly_count']}")
            click.echo(f"   当日计数: {result['daily_count']}")
            if not result['allowed']:
                click.echo(f"   限制原因: {result.get('reason', '未知')}")
        except Exception as e:
            click.echo(f"❌ 检查失败: {e}")
    
    asyncio.run(_check_rate())


@email.command()
def config():
    """显示邮件配置"""
    click.echo("📧 邮件上传配置:")
    click.echo(f"   启用状态: {'✅ 已启用' if settings.EMAIL_UPLOAD_ENABLED else '❌ 未启用'}")
    click.echo(f"   SMTP主机: {settings.SMTP_HOST or '未配置'}")
    click.echo(f"   IMAP主机: {settings.IMAP_HOST or '未配置'}")
    click.echo(f"   允许的域名: {', '.join(settings.ALLOWED_EMAIL_DOMAINS)}")
    click.echo(f"   最大附件数: {settings.MAX_EMAIL_ATTACHMENTS}")
    click.echo(f"   最大附件大小: {settings.MAX_ATTACHMENT_SIZE / 1024 / 1024:.1f}MB")
    click.echo(f"   小时频率限制: {settings.EMAIL_RATE_LIMIT_HOURLY}")
    click.echo(f"   日频率限制: {settings.EMAIL_RATE_LIMIT_DAILY}")
    click.echo(f"   检查间隔: {settings.EMAIL_CHECK_INTERVAL}秒")
    click.echo(f"   Redis启用: {'✅ 已启用' if settings.REDIS_ENABLED else '❌ 未启用'}")


@email.command()
@click.option('--enable/--disable', default=True, help='启用或禁用邮件上传')
def toggle(enable):
    """切换邮件上传功能状态"""
    # 注意：这个命令只是演示，实际上需要修改配置文件或环境变量
    status = "启用" if enable else "禁用"
    click.echo(f"{'✅' if enable else '❌'} 邮件上传功能已{status}")
    click.echo("注意：请在配置文件或环境变量中设置 EMAIL_UPLOAD_ENABLED 来永久更改此设置")


if __name__ == '__main__':
    email()