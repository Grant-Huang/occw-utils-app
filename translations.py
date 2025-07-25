# -*- coding: utf-8 -*-
"""
多语言翻译配置
"""

TRANSLATIONS = {
    'zh': {
        # 系统基础
        'system_name': 'OCCW报价单转换系统',
        'company_name': '加西欧派',
        'company_full_name': 'Oppein Cabinet Canada West Ltd.',
        'copyright': '© 2025 OCCW报价单转换系统 - 加西欧派',
        
        # 导航菜单
        'nav_home': '主页',
        'nav_prices': '价格管理',
        'nav_config': '配置',
        'nav_mappings': 'SKU映射',
        'nav_help': '帮助',
        'nav_admin_login': '管理员登录',
        'nav_admin_logout': '退出',
        'nav_language': '语言',
        
        # 主页
        'home_title': '主页',
        'upload_pdf_title': '上传2020软件报价单PDF',
        'upload_pdf_desc': '请选择要转换的2020软件报价单PDF文件',
        'select_file': '选择文件',
        'upload_button': '上传并解析',
        'quotation_table_title': '报价单表格',
        'export_excel': '导出Excel',
        'export_csv': '导出CSV',
        'export_pdf': '导出PDF',
        'show_raw_text': '显示PDF原始文本',
        
        # 表格列头
        'col_seq': '序号',
        'col_code': 'Code',
        'col_sku': 'SKU',
        'col_qty': '数量',
        'col_color': '花色',
        'col_2020_price': '2020单价',
        'col_2020_total': '2020总价',
        'col_occw_sku': 'OCCW SKU',
        'col_occw_price': 'OCCW单价',
        'col_occw_total': 'OCCW总价',
        'total_2020': '2020合计',
        'total_occw': 'OCCW合计',
        
        # 通用
        'loading': '加载中...',
        'save': '保存',
        'cancel': '取消',
        'edit': '编辑',
        'delete': '删除',
        'confirm': '确认',
        'success': '成功',
        'error': '错误',
        'warning': '警告',
        'info': '信息',
        
        # 权限
        'login': '登录',
        'password': '密码',
        'admin_required': '需要管理员权限',
        'login_success': '登录成功',
        'login_failed': '登录失败',
        'password_error': '密码错误',
        
        # SKU映射
        'sku_mappings_title': 'SKU映射管理',
        'mapping_list': '映射关系列表',
        'original_sku': '原始SKU',
        'mapped_sku': '映射SKU',
        'no_mappings': '暂无SKU映射关系',
        'loading_mappings': '正在加载映射数据...',
        
        # 消息
        'upload_success': '文件上传成功',
        'upload_failed': '文件上传失败',
        'parse_success': '解析成功',
        'parse_failed': '解析失败',
        'save_success': '保存成功',
        'save_failed': '保存失败',
        
        # 帮助页面
        'help_title': '帮助文档',
        'help_system_intro': '系统介绍',
        'help_system_intro_desc': 'OCCW报价单转换系统是一个专业的PDF报价单处理工具，专为加西欧派(Oppein Cabinet Canada West Ltd.)设计，用于将2020软件生成的报价单转换为标准化的OCCW格式。',
        'help_main_features': '主要功能',
        'help_pdf_upload': 'PDF文件上传',
        'help_pdf_upload_desc': '支持上传2020软件生成的PDF报价单文件',
        'help_auto_parse': '智能解析',
        'help_auto_parse_desc': '自动识别PDF中的产品信息、数量、价格等数据',
        'help_sku_generation': 'SKU生成',
        'help_sku_generation_desc': '根据预设规则自动生成OCCW标准SKU编码',
        'help_price_management': '价格管理',
        'help_price_management_desc': '管理OCCW标准价格表，支持Excel格式导入',
        'help_multi_export': '多格式导出',
        'help_multi_export_desc': '支持导出为Excel、CSV、PDF等多种格式',
        'help_multilang': '多语言支持',
        'help_multilang_desc': '支持中文、英语、法语三种界面语言',
        'help_usage_guide': '使用指南',
        'help_step1': '第1步：上传PDF文件',
        'help_step1_desc': '在主页点击"选择文件"按钮，选择2020软件生成的报价单PDF文件，然后点击"上传并解析"。',
        'help_step2': '第2步：检查解析结果',
        'help_step2_desc': '系统会自动解析PDF内容并显示产品表格，请检查解析结果是否正确。',
        'help_step3': '第3步：调整SKU映射',
        'help_step3_desc': '如需要，可以在SKU映射管理页面调整产品的SKU对应关系。',
        'help_step4': '第4步：导出结果',
        'help_step4_desc': '确认无误后，可以将结果导出为Excel、CSV或PDF格式。',
        'help_permissions': '权限说明',
        'help_normal_users': '普通用户权限',
        'help_normal_users_desc': '可以上传解析PDF、查看结果、导出文件、查看帮助文档',
        'help_admin_users': '管理员权限',
        'help_admin_users_desc': '除普通用户权限外，还可以管理OCCW价格表、配置SKU规则、管理SKU映射关系',
        'help_technical_support': '技术支持',
        'help_contact_info': '联系信息',
        'help_email_support': '邮件支持',
        'help_phone_support': '电话支持',
        'help_company_info': '公司信息',
        'help_company_name': '加西欧派',
        'help_company_full': 'Oppein Cabinet Canada West Ltd.',
        'help_version_info': '版本信息',
        'help_current_version': '当前版本',
    },
    
    'en': {
        # System Basic
        'system_name': 'OCCW Quote Conversion System',
        'company_name': 'Oppein West',
        'company_full_name': 'Oppein Cabinet Canada West Ltd.',
        'copyright': '© 2025 OCCW Quote Conversion System - Oppein Cabinet Canada West Ltd.',
        
        # Navigation
        'nav_home': 'Home',
        'nav_prices': 'Price Management',
        'nav_config': 'Configuration',
        'nav_mappings': 'SKU Mappings',
        'nav_help': 'Help',
        'nav_admin_login': 'Admin Login',
        'nav_admin_logout': 'Logout',
        'nav_language': 'Language',
        
        # Home Page
        'home_title': 'Home',
        'upload_pdf_title': 'Upload 2020 Software Quote PDF',
        'upload_pdf_desc': 'Please select the 2020 software quote PDF file to convert',
        'select_file': 'Select File',
        'upload_button': 'Upload & Parse',
        'quotation_table_title': 'Quote Table',
        'export_excel': 'Export Excel',
        'export_csv': 'Export CSV',
        'export_pdf': 'Export PDF',
        'show_raw_text': 'Show Raw PDF Text',
        
        # Table Headers
        'col_seq': 'Seq',
        'col_code': 'Code',
        'col_sku': 'SKU',
        'col_qty': 'Qty',
        'col_color': 'Color',
        'col_2020_price': '2020 Price',
        'col_2020_total': '2020 Total',
        'col_occw_sku': 'OCCW SKU',
        'col_occw_price': 'OCCW Price',
        'col_occw_total': 'OCCW Total',
        'total_2020': '2020 Total',
        'total_occw': 'OCCW Total',
        
        # Common
        'loading': 'Loading...',
        'save': 'Save',
        'cancel': 'Cancel',
        'edit': 'Edit',
        'delete': 'Delete',
        'confirm': 'Confirm',
        'success': 'Success',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Info',
        
        # Authentication
        'login': 'Login',
        'password': 'Password',
        'admin_required': 'Administrator privileges required',
        'login_success': 'Login successful',
        'login_failed': 'Login failed',
        'password_error': 'Incorrect password',
        
        # SKU Mappings
        'sku_mappings_title': 'SKU Mapping Management',
        'mapping_list': 'Mapping List',
        'original_sku': 'Original SKU',
        'mapped_sku': 'Mapped SKU',
        'no_mappings': 'No SKU mappings found',
        'loading_mappings': 'Loading mapping data...',
        
        # Messages
        'upload_success': 'File uploaded successfully',
        'upload_failed': 'File upload failed',
        'parse_success': 'Parsing successful',
        'parse_failed': 'Parsing failed',
        'save_success': 'Saved successfully',
        'save_failed': 'Save failed',
        
        # Help Page
        'help_title': 'Help Documentation',
        'help_system_intro': 'System Introduction',
        'help_system_intro_desc': 'OCCW Quote Conversion System is a professional PDF quotation processing tool designed specifically for Oppein Cabinet Canada West Ltd., used to convert quotations generated by 2020 software into standardized OCCW format.',
        'help_main_features': 'Main Features',
        'help_pdf_upload': 'PDF File Upload',
        'help_pdf_upload_desc': 'Supports uploading PDF quotation files generated by 2020 software',
        'help_auto_parse': 'Intelligent Parsing',
        'help_auto_parse_desc': 'Automatically recognizes product information, quantities, prices and other data in PDFs',
        'help_sku_generation': 'SKU Generation',
        'help_sku_generation_desc': 'Automatically generates OCCW standard SKU codes according to preset rules',
        'help_price_management': 'Price Management',
        'help_price_management_desc': 'Manages OCCW standard price lists, supports Excel format import',
        'help_multi_export': 'Multi-format Export',
        'help_multi_export_desc': 'Supports export to Excel, CSV, PDF and other formats',
        'help_multilang': 'Multi-language Support',
        'help_multilang_desc': 'Supports Chinese, English, and French interface languages',
        'help_usage_guide': 'Usage Guide',
        'help_step1': 'Step 1: Upload PDF File',
        'help_step1_desc': 'On the homepage, click "Select File" button, choose a quotation PDF file generated by 2020 software, then click "Upload & Parse".',
        'help_step2': 'Step 2: Check Parsing Results',
        'help_step2_desc': 'The system will automatically parse the PDF content and display the product table. Please check if the parsing results are correct.',
        'help_step3': 'Step 3: Adjust SKU Mappings',
        'help_step3_desc': 'If needed, you can adjust the SKU correspondence of products in the SKU Mapping Management page.',
        'help_step4': 'Step 4: Export Results',
        'help_step4_desc': 'After confirmation, you can export the results to Excel, CSV or PDF format.',
        'help_permissions': 'Permission Instructions',
        'help_normal_users': 'Regular User Permissions',
        'help_normal_users_desc': 'Can upload and parse PDFs, view results, export files, and view help documentation',
        'help_admin_users': 'Administrator Permissions',
        'help_admin_users_desc': 'In addition to regular user permissions, can also manage OCCW price lists, configure SKU rules, and manage SKU mapping relationships',
        'help_technical_support': 'Technical Support',
        'help_contact_info': 'Contact Information',
        'help_email_support': 'Email Support',
        'help_phone_support': 'Phone Support',
        'help_company_info': 'Company Information',
        'help_company_name': 'Oppein West',
        'help_company_full': 'Oppein Cabinet Canada West Ltd.',
        'help_version_info': 'Version Information',
        'help_current_version': 'Current Version',
    },
    
    'fr': {
        # Système de base
        'system_name': 'Système de Conversion de Devis OCCW',
        'company_name': 'Oppein Ouest',
        'company_full_name': 'Oppein Cabinet Canada West Ltd.',
        'copyright': '© 2025 Système de Conversion de Devis OCCW - Oppein Cabinet Canada West Ltd.',
        
        # Navigation
        'nav_home': 'Accueil',
        'nav_prices': 'Gestion des Prix',
        'nav_config': 'Configuration',
        'nav_mappings': 'Mappages SKU',
        'nav_help': 'Aide',
        'nav_admin_login': 'Connexion Admin',
        'nav_admin_logout': 'Déconnexion',
        'nav_language': 'Langue',
        
        # Page d'accueil
        'home_title': 'Accueil',
        'upload_pdf_title': 'Télécharger PDF de Devis 2020',
        'upload_pdf_desc': 'Veuillez sélectionner le fichier PDF de devis 2020 à convertir',
        'select_file': 'Sélectionner Fichier',
        'upload_button': 'Télécharger et Analyser',
        'quotation_table_title': 'Tableau de Devis',
        'export_excel': 'Exporter Excel',
        'export_csv': 'Exporter CSV',
        'export_pdf': 'Exporter PDF',
        'show_raw_text': 'Afficher Texte PDF Brut',
        
        # En-têtes de tableau
        'col_seq': 'Seq',
        'col_code': 'Code',
        'col_sku': 'SKU',
        'col_qty': 'Qté',
        'col_color': 'Couleur',
        'col_2020_price': 'Prix 2020',
        'col_2020_total': 'Total 2020',
        'col_occw_sku': 'SKU OCCW',
        'col_occw_price': 'Prix OCCW',
        'col_occw_total': 'Total OCCW',
        'total_2020': 'Total 2020',
        'total_occw': 'Total OCCW',
        
        # Commun
        'loading': 'Chargement...',
        'save': 'Enregistrer',
        'cancel': 'Annuler',
        'edit': 'Modifier',
        'delete': 'Supprimer',
        'confirm': 'Confirmer',
        'success': 'Succès',
        'error': 'Erreur',
        'warning': 'Avertissement',
        'info': 'Information',
        
        # Authentification
        'login': 'Connexion',
        'password': 'Mot de passe',
        'admin_required': 'Privilèges administrateur requis',
        'login_success': 'Connexion réussie',
        'login_failed': 'Échec de connexion',
        'password_error': 'Mot de passe incorrect',
        
        # Mappages SKU
        'sku_mappings_title': 'Gestion des Mappages SKU',
        'mapping_list': 'Liste des Mappages',
        'original_sku': 'SKU Original',
        'mapped_sku': 'SKU Mappé',
        'no_mappings': 'Aucun mappage SKU trouvé',
        'loading_mappings': 'Chargement des données de mappage...',
        
        # Messages
        'upload_success': 'Fichier téléchargé avec succès',
        'upload_failed': 'Échec du téléchargement',
        'parse_success': 'Analyse réussie',
        'parse_failed': 'Échec de l\'analyse',
        'save_success': 'Enregistré avec succès',
        'save_failed': 'Échec de l\'enregistrement',
        
        # Page d'aide
        'help_title': 'Documentation d\'Aide',
        'help_system_intro': 'Introduction du Système',
        'help_system_intro_desc': 'Le Système de Conversion de Devis OCCW est un outil professionnel de traitement de devis PDF conçu spécifiquement pour Oppein Cabinet Canada West Ltd., utilisé pour convertir les devis générés par le logiciel 2020 en format OCCW standardisé.',
        'help_main_features': 'Fonctionnalités Principales',
        'help_pdf_upload': 'Téléchargement de Fichier PDF',
        'help_pdf_upload_desc': 'Prend en charge le téléchargement de fichiers de devis PDF générés par le logiciel 2020',
        'help_auto_parse': 'Analyse Intelligente',
        'help_auto_parse_desc': 'Reconnaît automatiquement les informations produit, quantités, prix et autres données dans les PDF',
        'help_sku_generation': 'Génération de SKU',
        'help_sku_generation_desc': 'Génère automatiquement des codes SKU standard OCCW selon des règles prédéfinies',
        'help_price_management': 'Gestion des Prix',
        'help_price_management_desc': 'Gère les listes de prix standard OCCW, prend en charge l\'importation au format Excel',
        'help_multi_export': 'Export Multi-format',
        'help_multi_export_desc': 'Prend en charge l\'export vers Excel, CSV, PDF et autres formats',
        'help_multilang': 'Support Multilingue',
        'help_multilang_desc': 'Prend en charge les langues d\'interface chinoise, anglaise et française',
        'help_usage_guide': 'Guide d\'Utilisation',
        'help_step1': 'Étape 1: Télécharger le Fichier PDF',
        'help_step1_desc': 'Sur la page d\'accueil, cliquez sur le bouton "Sélectionner Fichier", choisissez un fichier de devis PDF généré par le logiciel 2020, puis cliquez sur "Télécharger et Analyser".',
        'help_step2': 'Étape 2: Vérifier les Résultats d\'Analyse',
        'help_step2_desc': 'Le système analysera automatiquement le contenu PDF et affichera le tableau des produits. Veuillez vérifier si les résultats d\'analyse sont corrects.',
        'help_step3': 'Étape 3: Ajuster les Mappages SKU',
        'help_step3_desc': 'Si nécessaire, vous pouvez ajuster la correspondance SKU des produits dans la page de Gestion des Mappages SKU.',
        'help_step4': 'Étape 4: Exporter les Résultats',
        'help_step4_desc': 'Après confirmation, vous pouvez exporter les résultats au format Excel, CSV ou PDF.',
        'help_permissions': 'Instructions de Permissions',
        'help_normal_users': 'Permissions Utilisateur Régulier',
        'help_normal_users_desc': 'Peut télécharger et analyser des PDF, voir les résultats, exporter des fichiers et consulter la documentation d\'aide',
        'help_admin_users': 'Permissions Administrateur',
        'help_admin_users_desc': 'En plus des permissions utilisateur régulier, peut également gérer les listes de prix OCCW, configurer les règles SKU et gérer les relations de mappage SKU',
        'help_technical_support': 'Support Technique',
        'help_contact_info': 'Informations de Contact',
        'help_email_support': 'Support par Email',
        'help_phone_support': 'Support Téléphonique',
        'help_company_info': 'Informations sur l\'Entreprise',
        'help_company_name': 'Oppein Ouest',
        'help_company_full': 'Oppein Cabinet Canada West Ltd.',
        'help_version_info': 'Informations sur la Version',
        'help_current_version': 'Version Actuelle',
    }
}

# 默认语言
DEFAULT_LANGUAGE = 'zh'

# 支持的语言
SUPPORTED_LANGUAGES = {
    'zh': '中文',
    'en': 'English', 
    'fr': 'Français'
}

def get_text(key, lang=DEFAULT_LANGUAGE):
    """获取翻译文本"""
    return TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE]).get(key, key) 