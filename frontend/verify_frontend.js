#!/usr/bin/env node

/**
 * 前端验证脚本
 * 检查前端组件和路由是否正常工作
 */

const fs = require('fs');
const path = require('path');

class FrontendVerifier {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.srcPath = path.join(__dirname, 'src');
  }

  log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = {
      'info': '✅',
      'warn': '⚠️',
      'error': '❌'
    };
    console.log(`${prefix[type]} ${message}`);
  }

  checkFileExists(filePath, description) {
    const fullPath = path.join(this.srcPath, filePath);
    if (fs.existsSync(fullPath)) {
      this.log(`${description} 存在: ${filePath}`);
      return true;
    } else {
      this.errors.push(`${description} 不存在: ${filePath}`);
      this.log(`${description} 不存在: ${filePath}`, 'error');
      return false;
    }
  }

  checkImportStatements(filePath, expectedImports) {
    const fullPath = path.join(this.srcPath, filePath);
    if (!fs.existsSync(fullPath)) {
      return false;
    }

    const content = fs.readFileSync(fullPath, 'utf8');
    let allImportsFound = true;

    expectedImports.forEach(importStatement => {
      if (content.includes(importStatement)) {
        this.log(`导入语句正确: ${importStatement}`);
      } else {
        this.warnings.push(`缺少导入语句: ${importStatement} in ${filePath}`);
        this.log(`缺少导入语句: ${importStatement} in ${filePath}`, 'warn');
        allImportsFound = false;
      }
    });

    return allImportsFound;
  }

  checkRoutes() {
    this.log('\n🔍 检查路由配置...');
    
    const appPath = 'App.tsx';
    if (!this.checkFileExists(appPath, 'App.tsx')) {
      return false;
    }

    const appContent = fs.readFileSync(path.join(this.srcPath, appPath), 'utf8');
    
    const expectedRoutes = [
      '/tracker',
      '/tracker-test',
      '/admin/login',
      '/admin/dashboard'
    ];

    expectedRoutes.forEach(route => {
      if (appContent.includes(`path="${route}"`)) {
        this.log(`路由配置正确: ${route}`);
      } else {
        this.warnings.push(`路由配置缺失: ${route}`);
        this.log(`路由配置缺失: ${route}`, 'warn');
      }
    });

    return true;
  }

  checkComponents() {
    this.log('\n🧩 检查组件文件...');
    
    const components = [
      { path: 'components/StatusIndicator.tsx', name: 'StatusIndicator组件' },
      { path: 'components/Toast.tsx', name: 'Toast组件' },
      { path: 'components/ErrorBoundary.tsx', name: 'ErrorBoundary组件' },
      { path: 'pages/TrackerQuery.tsx', name: 'TrackerQuery页面' },
      { path: 'pages/TrackerTest.tsx', name: 'TrackerTest页面' },
      { path: 'services/tracker.ts', name: 'Tracker服务' }
    ];

    let allComponentsExist = true;
    components.forEach(component => {
      if (!this.checkFileExists(component.path, component.name)) {
        allComponentsExist = false;
      }
    });

    return allComponentsExist;
  }

  checkUIComponents() {
    this.log('\n🎨 检查UI组件...');
    
    const uiComponents = [
      'components/ui/card.tsx',
      'components/ui/button.tsx',
      'components/ui/input.tsx',
      'components/ui/label.tsx',
      'components/ui/alert.tsx',
      'components/ui/badge.tsx',
      'components/ui/progress.tsx',
      'components/ui/separator.tsx'
    ];

    let allUIComponentsExist = true;
    uiComponents.forEach(component => {
      if (!this.checkFileExists(component, `UI组件 ${path.basename(component)}`)) {
        allUIComponentsExist = false;
      }
    });

    return allUIComponentsExist;
  }

  checkImports() {
    this.log('\n📦 检查导入语句...');
    
    // 检查TrackerQuery的导入
    this.checkImportStatements('pages/TrackerQuery.tsx', [
      "import StatusIndicator",
      "import TrackerService",
      "import { useToastHelpers }"
    ]);

    // 检查tracker服务的导入
    this.checkImportStatements('services/tracker.ts', [
      "import request from"
    ]);

    return true;
  }

  checkPackageJson() {
    this.log('\n📋 检查package.json...');
    
    const packagePath = path.join(__dirname, 'package.json');
    if (!fs.existsSync(packagePath)) {
      this.errors.push('package.json 不存在');
      this.log('package.json 不存在', 'error');
      return false;
    }

    const packageContent = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    
    const requiredDeps = [
      'react',
      'react-dom',
      'react-router-dom',
      'axios'
    ];

    const allDeps = { ...packageContent.dependencies, ...packageContent.devDependencies };
    
    requiredDeps.forEach(dep => {
      if (allDeps[dep]) {
        this.log(`依赖存在: ${dep}@${allDeps[dep]}`);
      } else {
        this.warnings.push(`缺少依赖: ${dep}`);
        this.log(`缺少依赖: ${dep}`, 'warn');
      }
    });

    return true;
  }

  checkTailwindConfig() {
    this.log('\n🎨 检查Tailwind配置...');
    
    const tailwindPath = path.join(__dirname, 'tailwind.config.js');
    if (fs.existsSync(tailwindPath)) {
      this.log('Tailwind配置文件存在');
      return true;
    } else {
      this.warnings.push('Tailwind配置文件不存在');
      this.log('Tailwind配置文件不存在', 'warn');
      return false;
    }
  }

  generateReport() {
    this.log('\n📊 验证报告');
    this.log('='.repeat(50));
    
    const totalIssues = this.errors.length + this.warnings.length;
    
    this.log(`错误数量: ${this.errors.length}`);
    this.log(`警告数量: ${this.warnings.length}`);
    this.log(`总问题数: ${totalIssues}`);

    if (this.errors.length > 0) {
      this.log('\n❌ 错误列表:');
      this.errors.forEach(error => {
        console.log(`  - ${error}`);
      });
    }

    if (this.warnings.length > 0) {
      this.log('\n⚠️ 警告列表:');
      this.warnings.forEach(warning => {
        console.log(`  - ${warning}`);
      });
    }

    if (totalIssues === 0) {
      this.log('\n🎉 前端验证通过！所有组件和配置都正常。');
      return true;
    } else if (this.errors.length === 0) {
      this.log('\n✅ 前端基本正常，但有一些警告需要关注。');
      return true;
    } else {
      this.log('\n❌ 前端存在错误，需要修复后才能正常运行。');
      return false;
    }
  }

  run() {
    this.log('🚀 开始前端验证...');
    this.log('='.repeat(50));

    this.checkComponents();
    this.checkUIComponents();
    this.checkRoutes();
    this.checkImports();
    this.checkPackageJson();
    this.checkTailwindConfig();

    return this.generateReport();
  }
}

// 运行验证
const verifier = new FrontendVerifier();
const success = verifier.run();

process.exit(success ? 0 : 1);