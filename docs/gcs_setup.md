# 教程：如何设置 Google Cloud Storage (GCS) 用于知识库存储

本文档将指导您如何设置一个 **Google Cloud Storage (GCS) 存储桶**，并授权您的本地应用访问它。我们将优先介绍**应用默认凭据 (Application Default Credentials - ADC)**，这是最简单、最推荐的本地开发授权方法。

## 方法一：应用默认凭据 (ADC) - 推荐

此方法将您的 Google 用户身份（例如 `costa9293@gmail.com`）安全地暴露给本地运行的应用，无需处理任何密钥文件。

### 第一步：安装 Google Cloud CLI (`gcloud`)

如果您尚未安装 `gcloud`，请根据您的操作系统，按照官方指南进行安装：

[https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)

### 第二步：通过 gcloud 登录

这是**一次性**的设置。打开您的终端或命令提示符，运行以下命令：

```bash
gcloud auth application-default login
```

*   您的浏览器将自动打开一个 Google 登录页面。
*   请使用您希望应用使用的 Google 账户（例如 `costa9293@gmail.com`）登录并授权。
*   成功后，您的凭据将被安全地存储在您的本地系统上。

### 第三步：创建 GCS 存储桶 (如果尚未创建)

1.  **打开 GCS 浏览器**: [https://console.cloud.google.com/storage/browser](https://console.cloud.google.com/storage/browser)
2.  **创建新存储桶**: 点击 **“+ 创建存储桶”**，并为其指定一个**全球唯一**的名称（例如 `my-knowledge-base-adc-bucket`）。您可以接受所有默认设置。

### 第四步：为您的用户账户授予存储桶权限

1.  **进入权限设置**: 在 GCS 浏览器中，找到您的存储桶，点击其名称，然后选择 **“权限”** 标签页。
2.  **授予访问权限**: 点击 **“+ 授予访问权限”**。
3.  **配置权限**:
    *   **新的主账号**: 输入您用于 `gcloud` 登录的**电子邮件地址**（例如 `costa9293@gmail.com`）。
    *   **选择角色**: 搜索并选择 **“Storage Object Admin” (存储对象管理员)**。
    *   点击 **“保存”**。

### 第五步：配置您的应用

现在，您的应用配置变得非常简单，**无需任何密钥文件**：

```python
gcs_config = {
    "auth_method": "adc", # 或者直接省略此行，因为 adc 是默认值
    "bucket_name": "your-globally-unique-bucket-name"
}

storage_agent = KnowledgeStorageAgent(
    provider_type='gcs', 
    provider_config=gcs_config
)
```

---

## 方法二：服务账户 (适用于生产/自动化环境)

如果您需要在服务器或 CI/CD 环境中运行此应用（没有人类用户可以登录），则应使用服务账户。

*   **创建服务账户**: 按照之前的指南创建服务账户并下载其 JSON 密钥文件。
*   **授予权限**: 在 GCS 存储桶的“权限”页面，将 **“Storage Object Admin”** 角色授予您的**服务账户的电子邮件地址**。
*   **配置应用**: 

    ```python
    gcs_config = {
        "auth_method": "service_account",
        "service_account_key_path": "path/to/your/key.json",
        "bucket_name": "your-bucket-name"
    }
    ```