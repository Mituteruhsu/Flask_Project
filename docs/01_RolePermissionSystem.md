<a name="HEAD"></a>
<p align="center">
  <img src="../assets/banner.svg" alt="CarbonProject Banner" width="100%">
</p>

[🧭專案導覽](../README.md#專案導覽)

# 第一章《角色權限系統》 (Role & Permission System)

## 📖 概要

說明本系統中的角色與權限設計原則、授權邏輯以及資料表結構。  
角色權限系統是整個 CarbonProject 的核心基礎之一，確保不同使用者依據身份存取相應功能與頁面，並提升系統的安全性與可維護性。把 RBAC（Role-Based Access Control） 擴充到「多層使用者類別」與「企業層級分權」的架構

---

## 🎯 設計目標

- **確保安全性**：限制未授權使用者的功能操作與資料存取。  
- **提升擴充性**：新增角色或權限時不需大幅修改原有程式碼。  
- **支援多層級角色**：區分「平台管理者」、「企業管理者」、「一般會員」等不同層級。  
- **集中管理**：透過資料庫與後台介面集中管理角色與權限關係。  

### 🔹 兩大類使用者

#### 一般使用者（Individual User）

- 例：註冊會員、平台個人使用者
- 權限範圍：僅限個人帳戶、查看個人資料、基本操作
- 常見角色：Member, Guest

#### 公司使用者（Company User）

- 例：企業帳號、公司登入者
- 權限根據職位細分：
  * **主管**（**Manager / Admin**）可審核、管理員工、設定公司目標
  * **非主管**（**Employee / Staff**）只能上傳、查看自己負責的資料

---

## 🧩 系統架構概念

### Role-Based Access Control（RBAC，基於角色的存取控制）  
是一種管理系統資源存取權限的方法，核心概念是把權限（Permissions）分配給角色（Roles），再把角色分配給使用者（Users），而不是直接把權限分配給每個使用者。這樣做可以大幅簡化權限管理，特別是當使用者數量多或權限複雜時。

### 對應 Controller 層

Controller 層
   │
   ├── AuthController → AuthService → RBACService (授權驗證)
   │                                    ↑
   │                                    └── CapabilityService (查詢能力點)
   │
   └── RbacController → RoleService / PermissionService → CapabilityService (管理介面)

- AuthController / Middleware 調用：
    - RBACService 內可能會調用 CapabilityService 來確認某使用者是否有該功能的 Capability。
- RbacController（管理介面）：
    - 用於建立 / 修改 / 查看 Capability。
    - 也會用來將 Capability 與 Permission 綁定。

| Service           | 主要用途                   | Controller 呼叫方式            |
| ----------------- | ---------------------- | -------------------------- |
| RoleService       | 角色 CRUD、角色分配使用者        | RbacController             |
| PermissionService | 權限 CRUD、綁定角色           | RbacController             |
| CapabilityService | 功能點 CRUD、綁定 Permission | RbacController、RBACService |
| RBACService       | 授權檢查、使用者權限整合           | AuthController、Middleware  |

---

角色權限系統採用 **Role-Based Access Control (RBAC)** 模型實作，  
結構如下圖所示：

```mermaid
flowchart TB
  subgraph Users["使用者 (Users)"]
    GU([一般使用者])
    CU([公司使用者])
    M([主管])
    E([非主管])
  end

  subgraph Roles["角色 (Roles)"]
    R1[Member]
    R2[ManagerRole]
    R3[EmployeeRole]
  end

  subgraph Permissions["權限 (Permissions)"]
    P1["ViewProfile / EditProfile"]
    P2["ApproveReports / ManageEmployee"]
    P3["UploadReport / ViewTask"]
  end

  subgraph Capabilities["能力 (Capabilities / API)"]
    C1["GET /user/profile\nPUT /user/profile"]
    C2["POST /company/reports/approve\nPUT /company/users/{id}"]
    C3["POST /company/reports/upload\nGET /company/tasks"]
  end

  GU --> R1
  CU --> R2
  CU --> R3
  M --> R2
  E --> R3

  R1 --> P1
  R2 --> P2
  R3 --> P3

  P1 --> C1
  P2 --> C2
  P3 --> C3
```

---
## 🧩 RBAC（角色導向存取控制）整合資料庫關聯圖（ERD）
```mermaid
erDiagram
    Members {
        int MemberId PK
        string Name
        string Email
        string PasswordHash
        datetime CreatedAt
    }

    Roles {
        int RoleId PK
        string RoleName
        string Description
    }

    UserRole {
        int MemberId FK
        int RoleId FK
    }

    Permissions {
        int PermissionId PK
        string PermissionKey
        string Description
    }

    RolePermission {
        int RoleId FK
        int PermissionId FK
    }

    Capabilities {
        int CapabilityId PK
        string CapabilityKey
        string Description
    }

    PermissionCapability {
        int PermissionId FK
        int CapabilityId FK
    }

    %% 關聯關係
    Members ||--o{ UserRole : "擁有"
    Roles ||--o{ UserRole : "被指派"
    Roles ||--o{ RolePermission : "擁有"
    Permissions ||--o{ RolePermission : "被包含"
    Permissions ||--o{ PermissionCapability : "具備"
    Capabilities ||--o{ PermissionCapability : "屬於"

```
---

## 🧩 RBAC 授權流程圖
```mermaid
---
config:
  theme: redux-dark
---
flowchart TB
    U[User] 
    subgraph Middleware["ASP.NET Core Middleware Pipeline"]
        direction LR
        AuthM["Authentication Middleware<br>(驗證 JWT / Cookies)"]
        PolicyM["Authorization Middleware<br>(比對角色與權限 Policy)"]
    end    
    subgraph Controllers["Controllers 層"]
        direction LR
        AuthC["AuthController<br>(登入 / 登出 / Token 發行)"]
        AC["ActionsController<br>(企業碳行動管理)"]
        DG["DataGoalsController<br>(碳目標設定與查詢)"]
    end
    
    subgraph Services["Service & Repository 層"]
        direction LR
        AuthS["AuthService<br>(帳密驗證 / Token 簽發)"]
        RoleS["RoleService<br>(角色 / 權限查詢)"]
        Repo["Repository<br>(資料庫存取層)"]
    end
    subgraph Database["Database (SQL Server)"]
        direction LR
        DB_M["Members"]
        DB_R["Roles / RolePermissions"]
        DB_P["Permissions / Capabilities"]
    end
    U -->|登入請求 /login| AuthC:::green
    AuthC -->|驗證帳號密碼| AuthS:::green
    AuthS -->|查詢角色與權限| RoleS:::green
    RoleS --> DB_R:::green
    RoleS --> DB_P:::green
    AuthS -->|回傳簽發 JWT Token| AuthC:::green
    AuthC -->|回傳 Token| U:::purple
    U -->|帶 JWT Token 請求| AuthM:::blue
    AuthM -->|還原 ClaimsPrincipal| PolicyM:::blue
    PolicyM -->|"若符合 Policy(Action.Create)"| AC:::blue
    PolicyM -->|"若符合 Policy(DataGoals.View)"| DG:::blue
    PolicyM -.->|查詢或更新資料| Repo:::blue
    Repo --> DB_M:::blue
    Repo --> DB_R:::blue
    Repo --> DB_P:::blue
    Repo --> AC:::purple
    Repo --> DG:::purple
    AC -->|回傳資料| U:::purple
    DG -->|回傳資料| U:::purple
    PolicyM -.->|"403 Forbidden (權限不足)"| U:::red
    classDef green stroke:#2ecc71,stroke-width:2px,color:#2ecc71;
    classDef blue stroke:#3498db,stroke-width:2px,color:#3498db;
    classDef purple stroke:#9b59b6,stroke-width:2px,color:#9b59b6;
    classDef red stroke:#e74c3c,stroke-width:2px,color:#e74c3c;

```

---

## 🧱 RBAC 四層關係：User → Role → Permission → Capability
| 層級 | 名稱 | 說明 |
|:-----|:-----|:-----|
| 👤 User（使用者） | 系統中的實際帳號 | Alice、Bob、管理員帳號 |
| 🎭 Role（角色） | 代表一組職責或身分，擁有一組權限 | Admin、Editor、Viewer |
| 🔐 Permission（權限） | 對系統資源的操作授權 | Article.Edit, User.Delete |
| ⚙️ Capability（能力 / 動作細項） | 具體可執行的功能或 API 操作	 | POST /articles/edit, DELETE /users/{id} |

### 範例
|	使用者	|	角色	|	權限	|	能力	|
| ----- | ------ | ----------- | ------------------- |
| Alice | Admin  | ManageUsers | DELETE /users/{id}  |
| Bob   | Editor | EditArticle | POST /articles/edit |
| Carol | Viewer | ViewArticle | GET /articles/{id}  |

| 使用者類型 | 角色       | 權限 (Permission) | 能力 (Capability / API)         |
| ----- | -------- | --------------- | ----------------------------- |
| 一般使用者 | Member   | ViewProfile     | GET /user/profile             |
| 一般使用者 | Member   | EditProfile     | PUT /user/profile             |
| 公司主管  | Manager  | ApproveReports  | POST /company/reports/approve |
| 公司主管  | Manager  | ManageEmployee  | PUT /company/users/{id}       |
| 公司員工  | Employee | UploadReport    | POST /company/reports/upload  |
| 公司員工  | Employee | ViewTask        | GET /company/tasks            |

---

## 🧠 為什麼要多一層 Capability？

一般的 RBAC 模型會停在「Role → Permission」，但實際系統中：
- Permission 是抽象的（邏輯層）
- Capability 是具體的（技術層 / API 或程式層）

例如：
> 「文章編輯權限（Permission）」  
> 對應到實際程式的 POST /api/article/edit（Capability）

這樣能讓：
- 權限邏輯與程式端操作解耦
- 更容易對接 REST API、微服務、或行為審計系統
- 安全審查更細緻：哪個角色觸發了哪個 API

---

> 📎 延伸閱讀  
  [第二章《使用者認證與註冊系統》](../docs/02_UserAuthAndRegister.md)  
  [第三章《JWT 記住我功能》](../docs/03_JWTRememberMe.md)  
  [第四章《Claims-based 認證流程》](../docs/04_ClaimsBasedAuthenticationFlow.md)  

---

[🌾頁首](#HEAD)