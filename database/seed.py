from werkzeug.security import generate_password_hash
from core.database import db
from database.models.user import User
from database.models.RBAC.role import Role
from database.models.RBAC.permission import Permission
from database.models.RBAC.capability import Capability
from database.models.subscription.plan import Plan


# =======================
#       預設資料建立
# =======================
class DatabaseSeeder:
    # 預設 user 資料建立 admin
    @staticmethod
    def seed_admin_user():
        """ 檢查 users 資料表，若無人則自動建立第一個 admin """
        print("檢查 users 資料表，若無人則自動建立第一個 admin")
        try:
            admin_exists = User.query.filter_by(role='admin').first()
            if not admin_exists:
                # 安全地產生密碼雜湊
                hashed_password = generate_password_hash("admin123")
                default_admin = User(
                    username="admin",
                    email="admin@example.com",
                    password_hash=hashed_password,
                    role="admin"
                )
                db.session.add(default_admin)
                db.session.commit()
                print("🎉 預設管理員建立成功！(帳號: admin / 密碼: admin123)")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 建立預設管理員帳號失敗: {e}")
    
    @staticmethod
    def seed_roles():
        """
        系統角色 (Role) 與 Role<->Permission 對應。

        注意：目前 User 表只有簡單的 role 字串欄位（admin/user），
        還沒有 User <-> Role 的正式關聯表，所以這裡先把 Role/Permission 的
        「資料」建好，方便你之後要做更細的功能權限時，直接加一張
        user_roles 關聯表就能接上，不用重新設計 Role 本身。

        角色命名故意跟 FamilyMember.FamilyRole 的 value 對齊（parent/child/viewer），
        方便未來要接軌時，可以直接用 family_role.value 去查對應的 Role。
        """
        print("檢查 roles 資料表，若無資料則建立預設角色與權限對應")
        try:
            role_permission_map = {
                "parent": ["invoice.view", "invoice.create", "invoice.edit", "invoice.delete", "invoice.export"],
                "child": ["invoice.view", "invoice.create", "invoice.edit", "invoice.export"],
                "viewer": ["invoice.view"],
            }
            role_descriptions = {
                "parent": "家長：可管理成員、編輯/刪除所有帳目、設定方案",
                "child": "小孩：可新增/編輯自己的帳目，不能刪除",
                "viewer": "唯讀家人：只能查看，不能異動",
            }

            for role_name, permission_names in role_permission_map.items():
                role = Role.query.filter_by(name=role_name).first()
                if not role:
                    role = Role(name=role_name, description=role_descriptions[role_name])
                    db.session.add(role)
                    db.session.flush()  # 先取得 role.id，才能建立多對多關聯

                # 補上這個角色目前缺少的 permission（避免重複新增已存在的關聯）
                existing_names = {p.name for p in role.permissions}
                for perm_name in permission_names:
                    if perm_name in existing_names:
                        continue
                    permission = Permission.query.filter_by(name=perm_name).first()
                    if permission:
                        role.permissions.append(permission)

            db.session.commit()
            print("🎉 預設 Role 與權限對應建立完成！")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 建立預設 Role 失敗: {e}")

    @staticmethod
    def seed_permissions():
        """
        系統功能權限 (Functional Permission)
        對應架構文件：invoice.create / invoice.edit / invoice.delete / invoice.export
        額外補上 invoice.view，因為「唯讀家人 (viewer)」需要一個能查看、但不能異動的權限可以掛。
        """
        print("檢查 permissions 資料表，若無資料則建立預設權限")
        try:
            defaults = [
                ("invoice.view", "查看發票紀錄"),
                ("invoice.create", "新增發票紀錄"),
                ("invoice.edit", "編輯發票紀錄"),
                ("invoice.delete", "刪除發票紀錄"),
                ("invoice.export", "匯出發票紀錄"),
            ]
            for name, desc in defaults:
                if not Permission.query.filter_by(name=name).first():
                    db.session.add(Permission(name=name, description=desc))
            db.session.commit()
            print("🎉 預設 Permission 建立完成！")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 建立預設 Permission 失敗: {e}")

    @staticmethod
    def seed_capabilities():
        """
        系統能力權限 (System Capability)
        對應 database/models/RBAC/capability.py 的用途註解：OCR / AI_PARSE / AI_CATEGORY
        這一層是「Plan 能不能用某個功能」，跟下面的 Permission（使用者能不能做某個操作）是兩件事。
        """
        print("檢查 capabilities 資料表，若無資料則建立預設能力")
        try:
            defaults = [
                ("OCR", "圖片 OCR 文字辨識"),
                ("AI_PARSE", "AI 發票資料解析"),
                ("AI_CATEGORY", "AI 消費自動分類"),
            ]
            for name, desc in defaults:
                if not Capability.query.filter_by(name=name).first():
                    db.session.add(Capability(name=name, description=desc))
            db.session.commit()
            print("🎉 預設 Capability 建立完成！")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 建立預設 Capability 失敗: {e}")

    @staticmethod
    def seed_plans():
        """
        訂閱方案 (Plan) 與 Plan<->Capability 對應。
        對應 database/models/subscription/plan.py 的用途註解：free / pro / family_plus

        價格是先放的預設值（新台幣月費），正式定價前請自行調整。
        """
        print("檢查 plans 資料表，若無資料則建立預設方案")
        try:
            plan_capability_map = {
                "free": (0, 4, ["OCR"]),
                "pro": (99, 6, ["OCR", "AI_PARSE"]),
                "family_plus": (199, 10, ["OCR", "AI_PARSE", "AI_CATEGORY"]),
            }
            plan_descriptions = {
                "free": "免費方案：基礎 OCR 辨識，最多 4 位家庭成員",
                "pro": "進階方案：OCR + AI 資料解析，最多 6 位家庭成員",
                "family_plus": "家庭旗艦方案：OCR + AI 解析 + AI 消費分類，最多 10 位家庭成員",
            }

            for plan_name, (price, max_members, capability_names) in plan_capability_map.items():
                plan = Plan.query.filter_by(name=plan_name).first()
                if not plan:
                    plan = Plan(
                        name=plan_name,
                        price=price,
                        max_members=max_members,
                        description=plan_descriptions[plan_name],
                    )
                    db.session.add(plan)
                    db.session.flush()  # 先取得 plan.id，才能建立多對多關聯

                existing_names = {c.name for c in plan.capabilities}
                for cap_name in capability_names:
                    if cap_name in existing_names:
                        continue
                    capability = Capability.query.filter_by(name=cap_name).first()
                    if capability:
                        plan.capabilities.append(capability)

            db.session.commit()
            print("🎉 預設 Plan 與能力對應建立完成！")
        except Exception as e:
            db.session.rollback()
            print(f"❌ 建立預設 Plan 失敗: {e}")

    def seed_invoice_categories():
        pass  # 之後加入 invoice_categories 資料表的預設資料

    def seed_family_members():
        pass  # 之後加入 family_members 資料表的預設資料

    def seed_system_settings():
        pass  # 之後加入 system_settings 資料表的預設資料