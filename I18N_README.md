# OCCW报价系统国际化(i18n)实现

## 概述

本项目已成功集成Flask-Babel国际化框架，支持中文(zh)、英文(en)、法文(fr)三种语言。

## 技术架构

- **框架**: Flask-Babel 4.0.0
- **翻译格式**: .po/.mo文件
- **支持语言**: 中文(zh)、英文(en)、法文(fr)
- **默认语言**: 中文(zh)

## 目录结构

```
translations/
├── zh/LC_MESSAGES/
│   ├── messages.po
│   └── messages.mo
├── en/LC_MESSAGES/
│   ├── messages.po
│   └── messages.mo
└── fr/LC_MESSAGES/
    ├── messages.po
    └── messages.mo
```

## 使用方法

### 1. 在Python代码中使用翻译

```python
from flask_babel import gettext as _

# 简单翻译
message = _('hello_world')

# 带参数的翻译
message = _('welcome_user').format(username='John')
```

### 2. 在Jinja2模板中使用翻译

```html
<!-- 简单翻译 -->
<h1>{{ _('page_title') }}</h1>

<!-- 带参数的翻译 -->
<p>{{ _('welcome_message').format(username=user.name) }}</p>
```

### 3. 语言切换

用户可以通过以下方式切换语言：

1. **URL参数**: `/set_language/zh`、`/set_language/en`、`/set_language/fr`
2. **Session存储**: 语言选择会保存在用户会话中
3. **浏览器语言**: 如果用户未选择语言，系统会自动检测浏览器语言

## 管理翻译

### 添加新的翻译键

1. 在代码中使用 `_('new_key')` 或 `{{ _('new_key') }}`
2. 运行提取命令：`python manage_translations.py extract`
3. 编辑 `translations/*/LC_MESSAGES/messages.po` 文件
4. 运行编译命令：`python manage_translations.py compile`

### 更新翻译

```bash
# 提取新的翻译键
python manage_translations.py extract

# 更新现有翻译文件
python manage_translations.py update

# 编译翻译文件
python manage_translations.py compile

# 或者一次性执行所有步骤
python manage_translations.py all
```

### 手动编辑翻译文件

翻译文件位于 `translations/*/LC_MESSAGES/messages.po`，格式如下：

```po
msgid "hello_world"
msgstr "你好世界"

msgid "welcome_user"
msgstr "欢迎，{username}！"
```

## 配置说明

### app.py中的配置

```python
# Babel配置
app.config['BABEL_DEFAULT_LOCALE'] = 'zh'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
app.config['LANGUAGES'] = {
    'zh': '中文',
    'en': 'English',
    'fr': 'Français'
}

# 初始化Babel
babel = Babel(app)

# 语言选择器
def get_locale():
    if 'language' in session:
        return session['language']
    return request.accept_languages.best_match(app.config['LANGUAGES'].keys())

babel.init_app(app, locale_selector=get_locale)
```

### babel.cfg配置

```
[python: **.py]
[jinja2: **/templates/**.html]
extensions=jinja2.ext.autoescape,jinja2.ext.with_
```

## 迁移说明

### 从旧翻译系统迁移

项目已从自定义的 `translations.py` 系统迁移到Flask-Babel：

1. **旧系统**: 使用 `get_text(key, lang)` 函数
2. **新系统**: 使用 `_('key')` 函数

### 迁移步骤

1. ✅ 已安装Flask-Babel依赖
2. ✅ 已配置Babel设置
3. ✅ 已生成翻译文件
4. ✅ 已更新代码中的翻译调用
5. ✅ 已测试应用功能

## 注意事项

1. **翻译键命名**: 使用下划线分隔的小写字母，如 `page_title`、`welcome_message`
2. **参数传递**: 使用 `.format()` 方法传递参数
3. **复数形式**: 当前配置支持单数形式，如需复数支持请修改配置
4. **字符编码**: 所有翻译文件使用UTF-8编码

## 故障排除

### 常见问题

1. **翻译不显示**: 检查翻译键是否正确，确保已编译.mo文件
2. **语言切换不生效**: 检查session配置和语言选择器函数
3. **新翻译不生效**: 运行 `python manage_translations.py compile` 重新编译

### 调试技巧

1. 检查Flask应用的日志输出
2. 验证翻译文件是否正确加载
3. 确认语言选择器函数正常工作

## 扩展支持

如需添加新语言支持：

1. 在 `app.config['LANGUAGES']` 中添加新语言
2. 创建对应的翻译目录：`translations/新语言代码/LC_MESSAGES/`
3. 生成翻译文件：`pybabel init -i messages.pot -d translations -l 新语言代码`
4. 编辑翻译文件并编译

## 版本信息

- **Flask-Babel**: 4.0.0
- **Babel**: 2.17.0
- **实现日期**: 2025-08-08
- **支持语言**: 中文、英文、法文
