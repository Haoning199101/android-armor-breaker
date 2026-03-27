#!/bin/bash
# Android Armor Breaker - GitHub上传助手
# 作者: Trx-HaoNing
# 版本: 1.0.0

set -e

echo "🚀 Android Armor Breaker GitHub上传助手"
echo "========================================"

# 检查是否在正确目录
if [ ! -f "SKILL.md" ]; then
    echo "❌ 错误: 请确保您在 android-armor-breaker 目录中"
    exit 1
fi

echo "📁 技能目录: $(pwd)"
echo "📊 文件状态:"
ls -la | grep -v "^total" | grep -v "^drwx" | head -10

# 检查git状态
echo ""
echo "🔍 检查Git状态..."
if ! git status &>/dev/null; then
    echo "❌ 错误: 当前目录不是git仓库"
    exit 1
fi

# 显示当前分支和提交
CURRENT_BRANCH=$(git branch --show-current)
COMMIT_COUNT=$(git rev-list --count HEAD)
echo "✅ Git仓库正常"
echo "  当前分支: $CURRENT_BRANCH"
echo "  提交数量: $COMMIT_COUNT"
echo "  最新提交: $(git log --oneline -1)"

# 检查远程仓库配置
echo ""
echo "🔗 检查远程仓库..."
if git remote | grep -q origin; then
    REMOTE_URL=$(git remote get-url origin)
    echo "✅ 已配置远程仓库: $REMOTE_URL"
else
    echo "❌ 未配置远程仓库"
    echo "正在配置为: https://github.com/Haoning199101/android-armor-breaker.git"
    git remote add origin https://github.com/Haoning199101/android-armor-breaker.git
    REMOTE_URL=$(git remote get-url origin)
fi

# 重命名分支为main（如果是master）
if [ "$CURRENT_BRANCH" = "master" ]; then
    echo "🔄 重命名分支 master → main"
    git branch -M main
    CURRENT_BRANCH="main"
fi

echo ""
echo "📦 准备上传的技能内容:"
echo "----------------------------------------"
git ls-tree -r HEAD --name-only | while read file; do
    size=$(git cat-file -s HEAD:"$file" 2>/dev/null || echo "?")
    if [ "$size" != "?" ]; then
        human_size=$(numfmt --to=iec --suffix=B $size 2>/dev/null || echo "${size}B")
    else
        human_size="?"
    fi
    echo "  📄 $file ($human_size)"
done
echo "----------------------------------------"

# 尝试推送
echo ""
echo "🚀 尝试推送到GitHub..."
echo "注意: 这可能需要GitHub身份验证"

# 方法1: 尝试标准推送
echo "🔄 尝试方法1: 标准推送 (HTTPS)"
if timeout 30 git push -u origin "$CURRENT_BRANCH" 2>&1 | tee /tmp/git_push.log; then
    echo "✅ 成功推送到GitHub!"
    echo ""
    echo "🎉 Android Armor Breaker 已成功上传!"
    echo "🔗 访问地址: https://github.com/Haoning199101/android-armor-breaker"
    exit 0
else
    PUSH_ERROR=$(cat /tmp/git_push.log)
    echo "⚠️  标准推送失败"
    
    # 检查错误类型
    if echo "$PUSH_ERROR" | grep -q "Authentication failed"; then
        echo "🔐 需要GitHub身份验证"
    elif echo "$PUSH_ERROR" | grep -q "Repository not found"; then
        echo "❓ GitHub仓库不存在，请先在GitHub上创建仓库"
    else
        echo "❌ 推送错误: $PUSH_ERROR"
    fi
fi

# 提供认证选项
echo ""
echo "🔐 GitHub认证选项:"
echo "========================================"
echo "1. 🔑 使用GitHub访问令牌 (推荐)"
echo "   1) 访问: https://github.com/settings/tokens"
echo "   2) 点击 'Generate new token (classic)'"
echo "   3) 勾选 'repo' 权限"
echo "   4) 复制生成的令牌"
echo "   5) 运行: git push https://Haoning199101:TOKEN@github.com/Haoning199101/android-armor-breaker.git main"
echo ""
echo "2. 🔐 配置SSH密钥"
echo "   1) 运行: ssh-keygen -t ed25519 -C '您的邮箱@example.com'"
echo "   2) 复制公钥: cat ~/.ssh/id_ed25519.pub"
echo "   3) 添加到GitHub: https://github.com/settings/keys"
echo "   4) 配置SSH远程: git remote set-url origin git@github.com:Haoning199101/android-armor-breaker.git"
echo "   5) 运行: git push -u origin main"
echo ""
echo "3. 💾 使用git凭据存储"
echo "   1) 运行: git config --global credential.helper store"
echo "   2) 运行: git push -u origin main"
echo "   3) 第一次会提示输入用户名和密码"
echo ""
echo "4. 📝 手动上传步骤"
echo "   1) 访问: https://github.com/new"
echo "   2) 创建仓库: android-armor-breaker"
echo "   3) 不上传任何文件 (跳过README)"
echo "   4) 复制推送命令执行"

echo ""
echo "📋 已完成准备的文件:"
echo "  ✅ SKILL.md - OpenClaw技能文档 (12.2KB)"
echo "  ✅ README.md - 详细说明文档 (2.5KB)"
echo "  ✅ LICENSE - MIT许可证 (1.1KB)"
echo "  ✅ _meta.json - 技能元数据"
echo "  ✅ .gitignore - Git忽略规则"
echo "  ✅ .clawhub/origin.json - ClawHub来源信息"
echo "  ✅ scripts/ - 所有核心脚本"

echo ""
echo "💡 技能特色:"
echo "  • Frida-based Android脱壳技术"
echo "  • 商业级到企业级保护方案支持"
echo "  • APK加固分析与智能DEX提取"
echo "  • 已在ClawHub上发布"
echo "  • OpenClaw原生集成"

echo ""
echo "📞 如需进一步帮助，请提供:"
echo "  • GitHub访问令牌 (临时)"
echo "  • 或授权使用SSH密钥"
echo "  • 或完成上述认证步骤"

exit 1