from fastapi import APIRouter, HTTPException, Depends, status, Form
from datetime import datetime
from database import get_db_connection
from routers.auth import get_current_active_user, role_required, get_password_hash

router = APIRouter()

# create a new user account 
@router.post('/create', dependencies=[Depends(role_required(["admin"]))])
async def create_user(
    fullName: str = Form(...),
    username: str = Form(...),
    email: str = Form (...),
    password: str = Form(...),
    userRole: str = Form(...)
):
    if userRole not in ['admin', 'manager', 'staff']:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")

    hashed_password = get_password_hash(password)

    conn = await get_db_connection()
    cursor = await conn.cursor()

    try:
        await cursor.execute('''
            INSERT INTO Users (FullName, Username, Email, UserPassword, UserRole)
            VALUES (?, ?, ?, ?, ?)
        ''', (fullName, username, email, hashed_password, userRole))
        await conn.commit()
    finally:
        await cursor.close()
        await conn.close()

    return {'message': 'User created successfully!'}

# admin fetch active accs
@router.get('/list-accounts', dependencies=[Depends(role_required(['admin']))])
async def list_users():
    conn = await get_db_connection()
    cursor = await conn.cursor()

    await cursor.execute('''
        SELECT UserID, FullName, Username, Email, UserRole, CreatedAt
        FROM Users
        WHERE isDisabled = 0
    ''')
    users = await cursor.fetchall()
    await conn.close()

    return [{"userID": u[0], "fullName": u[1], "username": u[2], "email": u[3], "userRole": u[4], "createdAt": u[5]}
            for u in users]

# admin update user acc
@router.put("/update/{user_id}", dependencies=[Depends(role_required(['admin']))])
async def update_user(
    user_id: int,
    fullName: str | None = Form(None),
    email: str | None = Form(None),
    password: str | None = Form(None)
):
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    updates = []
    values = []

    if fullName:
        updates.append('FullName = ?')
        values.append(fullName)
    if email:
        updates.append('Email = ?')
        values.append(email)
    if password:
        hashed_password = get_password_hash(password)
        updates.append('UserPassword = ?')
        values.append(hashed_password)
    updates.append('CreatedAt = ?')
    values.append(datetime.utcnow())

    values.append(user_id)

    if updates:
        try:
            await cursor.execute(f'''
                UPDATE Users
                SET {', '.join(updates)}
                WHERE UserID = ? AND isDisabled = 0
            ''', (*values,))
            await conn.commit()
        finally:
            await cursor.close()
            await conn.close()

        return {'message': 'User updated successfully'}

    return {'message': 'No fields to update'}

# admin soft delete user account
@router.delete('/delete/{user_id}', dependencies=[Depends(role_required(['admin']))])
async def delete_user(user_id: int):
    conn = await get_db_connection()
    cursor = await conn.cursor()

    try:
        await cursor.execute('''
            UPDATE Users
            SET isDisabled = 1
            WHERE UserID = ?
        ''', (user_id,))
        await conn.commit()
    finally:
        await cursor.close()
        await conn.close()

    return {'message': 'User deleted successfully'}

# user update details
@router.put('/self-update', dependencies=[Depends(role_required(['staff', 'manager']))])
async def update_self(
    fullName: str | None = Form(None),
    password: str | None = Form(None),
    current_user=Depends(get_current_active_user)
):
    conn = await get_db_connection()
    cursor = await conn.cursor()
    
    updates = []
    values = []

    if fullName:
        updates.append("FullName = ?")
        values.append(fullName)
    if email:
        updates.append("Email = ?")
        values.append(email)
    if password:
        hashed_password = get_password_hash(password)
        updates.append("UserPassword = ?")
        values.append(hashed_password)
    updates.append('CreatedAt = ?')
    values.append(datetime.utcnow())

    values.append(current_user.username)

    if updates:
        try:
            await cursor.execute(f'''
                UPDATE Users
                SET {', '.join(updates)}
                WHERE Username = ? AND isDisabled = 0
            ''', (*values,))
            await conn.commit()
        finally:
            await cursor.close()
            await conn.close()

        return {'message': 'Your account details have been updated!'}

    return {'message': 'No fields to update'}
