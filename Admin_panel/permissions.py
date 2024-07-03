from sqlalchemy import select

from Admin_panel.models import Role


async def permission_admin(role_id, session) -> bool:
    query_role = select(Role).where(Role.id == role_id)
    res_role = await session.execute(query_role)
    result_role = res_role.scalar_one_or_none()
    if result_role and result_role.name.lower() == 'admin':
        return True
    else:
        return False
