# 教程：如何获取 Google Drive API 的 `credentials.json` 文件

本文档将一步步指导您如何从 Google Cloud Console 获取用于访问 Google Drive API 的 `credentials.json` 授权文件。

### 第一步：访问 Google Cloud Console 并创建项目

1.  **打开 Google Cloud Console**: 在您的浏览器中访问 [https://console.cloud.google.com/](https://console.cloud.google.com/)。
2.  **创建或选择项目**:
    *   如果您没有项目，点击页面顶部的项目选择下拉菜单，然后点击 **“新建项目”**。给您的项目起一个名字（例如 `My-Knowledge-Base-API`），然后点击 **“创建”**。
    *   如果您已有项目，请从下拉菜单中选择您希望使用的项目。

### 第二步：启用 Google Drive API

1.  **进入 API 库**: 在左侧的导航菜单（“汉堡”菜单 ☰）中，找到 **“API 和服务”** > **“库”**。
2.  **搜索 API**: 在搜索框中输入 `Google Drive API` 并按回车。
3.  **启用 API**: 在搜索结果中点击 “Google Drive API”，然后在新页面中点击蓝色的 **“启用”** 按钮。

### 第三步：配置 OAuth 同意屏幕

在创建凭据之前，您需要告诉 Google 您的应用信息，以便在授权时显示给用户。

1.  **进入 OAuth 同意屏幕**: 在左侧导航菜单中，选择 **“API 和服务”** > **“OAuth 同意屏幕”**。
2.  **选择用户类型**:
    *   **内部 (Internal)**: 如果您的 Google 账户属于 Google Workspace 组织，并且此应用仅供组织内部人员使用，请选择此项。
    *   **外部 (External)**: 如果应用将供任何拥有 Google 账户的用户使用，请选择此项。对于个人项目，通常选择此项。
3.  **填写应用信息**:
    *   **应用名称**: 给您的应用起一个用户能看懂的名字（例如 `知识库文档访问工具`）。
    *   **用户支持电子邮件**: 选择您的电子邮件地址。
    *   **开发者联系信息**: 再次输入您的电子邮件地址。
    *   点击 **“保存并继续”**。
4.  **范围 (Scopes)**: 您可以暂时跳过此步骤，直接点击 **“保存并继续”**。
5.  **测试用户 (Test Users)**:
    > **[!] 这是最关键的一步，也是解决“Google 未验证此应用”错误的直接方法。**
    > 
    如果您之前选择了“外部”用户类型，您必须在此处添加您的账户作为测试用户。
    *   点击 **“+ ADD USERS”** 按钮。
    *   在弹出的窗口中，输入您将用来登录和授权的 Google 账户的电子邮件地址（在您的情况下，是 `costa9293@gmail.com`）。
    *   点击 **“添加”**。在开发阶段，只有在这里列出的账户才能成功授权。
6.  **完成**: 点击 **“保存并继续”**，然后返回信息中心。

### 第四步：创建 OAuth 2.0 客户端 ID

这是获取 `credentials.json` 文件的核心步骤。

1.  **进入凭据页面**: 在左侧导航菜单中，选择 **“API 和服务”** > **“凭据”**。
2.  **创建新凭据**: 点击页面顶部的 **“+ 创建凭据”**，然后从下拉菜单中选择 **“OAuth 客户端 ID”**。
3.  **选择应用类型**: 在“应用类型”下拉菜单中，选择 **“桌面应用”**。
4.  **命名客户端**: 为您的客户端 ID 起一个名字（例如 `知识库桌面客户端`）。
5.  **创建**: 点击 **“创建”** 按钮。

### 第五步：下载 `credentials.json` 文件

1.  **下载文件**: 创建成功后，会弹出一个窗口，显示您的客户端 ID 和客户端密钥。点击右侧的 **“下载 JSON”** 按钮。
2.  **重命名并移动文件**:
    *   将下载的文件重命名为 `credentials.json`。
    *   将这个 `credentials.json` 文件移动到本项目的根目录下，或者您在配置中指定的任何 `credentials_path` 路径。

您现在已经成功获取了 `credentials.json` 文件！当您第一次运行使用 `GoogleDriveStorageProvider` 的程序时，系统会自动打开一个浏览器窗口，要求您登录并授权。成功授权后，`token.json` 文件便会自动生成。

> **安全警告**: `credentials.json` 文件包含敏感信息。**绝对不要**将它提交到 Git 或任何公共代码库中。请确保它已被添加到 `.gitignore` 文件中。
