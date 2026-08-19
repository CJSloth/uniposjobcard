from nicegui import ui, app
import database as db
import json
import pdf_generator as pdf_gen

def get_categories_list():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS inventory_categories (name TEXT PRIMARY KEY)")
        cursor.execute("SELECT name FROM inventory_categories")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            return ["All Categories"] + [r[0] for r in rows]
    except Exception:
        pass
    
    return [
        "All Categories",
        "Hardware / Terminals",
        "Monitors & Displays",
        "Scanners & Peripherals",
        "Accessories & Cables",
        "Services & Installs"
    ]

def create_admin_page():
    current_tech = app.storage.user.get('tech_name', '')
    user_role = app.storage.user.get('role', 'Technician')

    if not current_tech:
        ui.notify('Please sign in with your PIN first!', type='warning')
        ui.navigate.to('/')
        return

    ui.add_head_html('''
    <style>
    .q-card {
        border-radius: 14px !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
    }
    .q-btn {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }
    .q-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 86, 179, 0.15);
    }
    .q-field__control {
        border-radius: 8px !important;
    }
    </style>
    ''', shared=True)

    auth_info = {
        'status': True,
        'role': user_role,
        'tech_name': current_tech
    }
    build_admin_interface(auth_info)

def build_admin_interface(auth_info):
    user_role = auth_info['role']
    current_tech = auth_info['tech_name']

    with ui.card().classes('w-full max-w-5xl mx-auto p-4 my-4 bg-white shadow-xl rounded-lg text-sm') as admin_content_card:
        
        with ui.row().classes('w-full justify-between items-center border-b pb-3 mb-4'):
            with ui.column().classes('gap-0'):
                ui.label('UNIPOS RETAIL SOLUTIONS').classes('text-xl font-black text-blue-900')
                ui.label(f'System Administration & Portal — Logged in as: {current_tech} [{user_role}]').classes('text-xs text-gray-500 font-bold')
            
            ui.button('👈 Back to Job Card', on_click=lambda: ui.navigate.to('/')).props('outline dense icon=arrow_back')

        if user_role == 'Technician':
            ui.label(f'👤 Technician Profile & Personal History: {current_tech}').classes('font-bold text-base text-blue-900 mb-2')
            
            with ui.card().classes('w-full p-4 bg-slate-50 border gap-3 shadow-none'):
                techs_data = db.get_technicians_db()
                my_data = techs_data.get(current_tech, {})
                
                ui.label('Update Your Credentials & PIN').classes('font-bold text-xs text-blue-900')
                with ui.grid(columns=2).classes('w-full gap-2'):
                    my_email = ui.input(label='Assigned Email', value=my_data.get('authorized_email', '')).classes('w-full').props('outlined dense bg-white')
                    my_pin = ui.input(label='New PIN Code', password=True, placeholder='Enter new 4+ digit PIN').classes('w-full').props('outlined dense bg-white')

                def save_my_profile():
                    conn = db.get_connection()
                    conn.cursor().execute("UPDATE technicians SET authorized_email=?, pin_code=? WHERE name=?", 
                                          (my_email.value.strip(), my_pin.value.strip(), current_tech))
                    conn.commit()
                    conn.close()
                    ui.notify('Your profile and PIN have been updated successfully!', type='positive')

                ui.button('💾 Save Profile Changes', on_click=save_my_profile).props('dense color=primary').classes('text-xs font-bold w-40')

            ui.separator().classes('my-4')
            ui.label('📜 Your Past Job Cards History').classes('font-bold text-sm text-gray-800 mb-2')
            
            all_history = db.get_job_card_history()
            tech_jobs = [j for j in all_history if j['tech'] == current_tech]
            
            if tech_jobs:
                with ui.column().classes('w-full gap-2 max-h-[400px] overflow-y-auto'):
                    with ui.row().classes('w-full text-xs font-bold bg-slate-200 p-2 rounded gap-2'):
                        ui.label('JC No').classes('w-2/12')
                        ui.label('Date').classes('w-2/12')
                        ui.label('Client Store').classes('w-6/12')
                        ui.label('Grand Total').classes('w-2/12 text-right')
                    for job in tech_jobs:
                        with ui.row().classes('w-full items-center border-b pb-1 gap-2 text-xs bg-white p-1 rounded'):
                            ui.label(job['jc_no']).classes('w-2/12 font-bold text-blue-900')
                            ui.label(job['date_str']).classes('w-2/12 text-gray-600')
                            ui.label(job.get('client', 'N/A')).classes('w-6/12 font-medium truncate')
                            ui.label(f"R{job['total']:.2f}").classes('w-2/12 text-right font-bold text-green-700')
            else:
                ui.label('No past job cards found for your profile.').classes('text-xs text-gray-400 italic')

        else:
            with ui.tabs().classes('w-full') as tabs:
                tab_techs = ui.tab('Field Technicians & Fleet', icon='engineering')
                tab_stock = ui.tab('Stock & Pricing Master', icon='inventory_2')
                tab_clients = ui.tab('Clients & Contacts', icon='storefront')

            with ui.tab_panels(tabs, value=tab_techs).classes('w-full pt-4'):
                
                with ui.tab_panel(tab_techs):
                    def open_add_tech_fleet_dialog():
                        with ui.dialog() as add_tf_dlg, ui.card().classes('w-[500px] p-5 gap-4 bg-white'):
                            ui.label('➕ Add New Technician or Fleet Vehicle').classes('font-bold text-blue-900 text-base border-b pb-2 w-full')
                            
                            with ui.expansion('🚗 Add Fleet Vehicle', icon='directions_car').classes('w-full bg-slate-50 border rounded'):
                                with ui.column().classes('w-full p-2 gap-2'):
                                    new_veh_input = ui.input(label='Vehicle Reg No', placeholder='e.g. CA123456 or Nancy').classes('w-full').props('outlined dense bg-white')
                                    def add_new_vehicle():
                                        reg = (new_veh_input.value or "").strip().upper()
                                        current_vehs = db.get_vehicles()
                                        if reg and reg not in current_vehs:
                                            conn = db.get_connection()
                                            conn.cursor().execute("INSERT INTO vehicles (reg_no) VALUES (?)", (reg,))
                                            conn.commit()
                                            conn.close()
                                            new_veh_input.value = ''
                                            refresh_tech_table()
                                            ui.notify(f'Added new vehicle "{reg}" to database!', type='positive')
                                            add_tf_dlg.close()
                                    ui.button('Save Fleet Vehicle', on_click=add_new_vehicle).props('dense color=primary').classes('text-xs font-bold')

                            with ui.expansion('👤 Register New Technician', icon='person_add').classes('w-full bg-slate-50 border rounded'):
                                with ui.column().classes('w-full p-2 gap-2'):
                                    vehs_list = ["None"] + db.get_vehicles()
                                    t_name = ui.input(label='User/Technician Name').classes('w-full').props('outlined dense bg-white')
                                    t_role = ui.select(['Technician', 'Admin', 'Both'], label='Access Role', value='Technician').classes('w-full').props('outlined dense bg-white')
                                    t_email = ui.input(label='Email Address').classes('w-full').props('outlined dense bg-white')
                                    t_pin = ui.input(label='Security PIN', password=True).classes('w-full').props('outlined dense bg-white')
                                    t_veh = ui.select(vehs_list, label='Assigned Vehicle', value='None').classes('w-full').props('outlined dense bg-white')
                                    
                                    with ui.row().classes('w-full gap-2'):
                                        t_min = ui.number(label='JC Min', value=4000).classes('w-1/2').props('outlined dense bg-white')
                                        t_max = ui.number(label='JC Max', value=4999).classes('w-1/2').props('outlined dense bg-white')
                                    
                                    t_primary_dispatch = ui.checkbox('🌟 Primary Dispatch Admin').classes('text-xs font-bold')

                                    def add_tech():
                                        name = (t_name.value or "").strip()
                                        techs = db.get_technicians_db()
                                        if name and name not in techs:
                                            is_admin_val = 1 if t_role.value in ['Admin', 'Both'] else 0
                                            is_primary_val = 1 if (is_admin_val and t_primary_dispatch.value) else 0
                                            
                                            conn = db.get_connection()
                                            cursor = conn.cursor()
                                            if is_primary_val:
                                                cursor.execute("UPDATE technicians SET is_primary_dispatch = 0")

                                            v_val = None if t_veh.value == 'None' else t_veh.value
                                            cursor.execute('''
                                                INSERT INTO technicians 
                                                (name, role, assigned_vehicle, primary_min, primary_max, current_jc, authorized_email, pin_code, is_admin, is_primary_dispatch)
                                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                            ''', (
                                                name, t_role.value, v_val, int(t_min.value or 0), int(t_max.value or 0), 
                                                int(t_min.value or 0), (t_email.value or '').strip(), (t_pin.value or '').strip(), is_admin_val, is_primary_val
                                            ))
                                            conn.commit()
                                            conn.close()
                                            refresh_tech_table()
                                            ui.notify(f'Saved User "{name}" to Database!', type='positive')
                                            add_tf_dlg.close()

                                    ui.button('Save Technician', on_click=add_tech).props('dense color=primary').classes('text-xs font-bold')

                            with ui.row().classes('w-full justify-end mt-2'):
                                ui.button('Close', on_click=add_tf_dlg.close).props('flat dense')
                        add_tf_dlg.open()

                    with ui.row().classes('w-full justify-between items-center mb-3'):
                        ui.label('🚗 Fleet & Technician Operations').classes('font-bold text-sm text-blue-900')
                        ui.button('🍔 Add New Menu', on_click=open_add_tech_fleet_dialog).props('outline dense icon=menu color=primary').classes('text-xs font-bold')

                    fleet_badge_container = ui.row().classes('w-full gap-1 items-center mb-4 p-2 bg-slate-50 border rounded')
                    def refresh_fleet_badges():
                        fleet_badge_container.clear()
                        vehs = db.get_vehicles()
                        with fleet_badge_container:
                            ui.label('Active Fleet:').classes('text-xs font-bold text-gray-700 mr-2')
                            for v in vehs:
                                def remove_v(reg=v):
                                    if len(vehs) > 1:
                                        conn = db.get_connection()
                                        conn.cursor().execute("DELETE FROM vehicles WHERE reg_no = ?", (reg,))
                                        conn.commit()
                                        conn.close()
                                        refresh_tech_table()
                                        ui.notify(f'Removed vehicle {reg}', type='warning')

                                with ui.badge(v, color='blue-3').classes('text-blue-900 text-xs px-2 py-1 items-center gap-1'):
                                    ui.button('×', on_click=remove_v).props('flat dense size=xs color=negative')

                    refresh_fleet_badges()

                    ui.separator().classes('my-3')
                    ui.label('Active Users, Roles, PINs & Ranges').classes('font-bold text-sm text-gray-800 mb-2')

                    tech_table_container = ui.column().classes('w-full gap-3')

                    def refresh_tech_table():
                        tech_table_container.clear()
                        refresh_fleet_badges()
                        techs = db.get_technicians_db()
                        vehs_list = ["None"] + db.get_vehicles()

                        with tech_table_container:
                            for tech, data in techs.items():
                                with ui.card().classes('w-full p-4 border border-slate-300 bg-slate-50 shadow-sm gap-2'):
                                    with ui.row().classes('w-full justify-between items-center border-b pb-2'):
                                        ui.label(f"👤 {tech} [{data.get('role', 'Technician')}]").classes('font-bold text-base text-blue-900')
                                        
                                        with ui.row().classes('items-center gap-2'):
                                            if data.get('is_primary_dispatch'):
                                                ui.badge('🌟 Primary Dispatch', color='orange-8').classes('text-xs px-2 py-1')
                                            ui.badge(f"Current JC: JC-{data['current_jc']}", color='blue-9').classes('text-xs px-2 py-1')
                                            
                                            def confirm_delete_profile(t_name=tech):
                                                with ui.dialog() as del_dlg, ui.card().classes('w-80 p-4 gap-3 bg-white'):
                                                    ui.label(f'⚠️ Delete Profile?').classes('font-bold text-red-600 text-base')
                                                    ui.label(f'Are you sure you want to delete profile "{t_name}"?').classes('text-xs text-gray-700')
                                                    
                                                    def execute_delete():
                                                        conn = db.get_connection()
                                                        conn.cursor().execute("DELETE FROM technicians WHERE name = ?", (t_name,))
                                                        conn.commit()
                                                        conn.close()
                                                        del_dlg.close()
                                                        refresh_tech_table()
                                                        ui.notify(f'Deleted profile "{t_name}" successfully.', type='warning')

                                                    with ui.row().classes('w-full justify-end gap-2 mt-2'):
                                                        ui.button('Cancel', on_click=del_dlg.close).props('flat dense')
                                                        ui.button('YES, DELETE', on_click=execute_delete).props('color=negative dense font-bold')
                                                del_dlg.open()

                                            ui.button('🗑️ Delete', on_click=confirm_delete_profile).props('dense outline size=xs color=negative')

                                    with ui.grid(columns=4).classes('w-full gap-2'):
                                        r_sel = ui.select(['Technician', 'Admin', 'Both'], label='Role:', value=data.get('role', 'Technician')).classes('w-full').props('outlined dense bg-white')
                                        e_inp = ui.input(label='Email:', value=data.get('authorized_email', '')).classes('w-full').props('outlined dense bg-white')
                                        pin_inp = ui.input(label='PIN / Password:', value=data.get('pin_code', ''), password=True).classes('w-full').props('outlined dense bg-white')
                                        current_v = data.get('assigned_vehicle') if data.get('assigned_vehicle') in vehs_list else 'None'
                                        v_sel = ui.select(vehs_list, label='Vehicle:', value=current_v).classes('w-full').props('outlined dense bg-white')

                                    with ui.grid(columns=4).classes('w-full gap-2 items-center'):
                                        p_min = ui.number(label='JC Min:', value=data['primary_min']).classes('w-full').props('outlined dense bg-white')
                                        p_max = ui.number(label='JC Max:', value=data['primary_max']).classes('w-full').props('outlined dense bg-white')
                                        s_min = ui.number(label='Book Min:', value=data.get('secondary_book_min', 0)).classes('w-full').props('outlined dense bg-white')
                                        s_max = ui.number(label='Book Max:', value=data.get('secondary_book_max', 0)).classes('w-full').props('outlined dense bg-white')

                                    with ui.row().classes('w-full justify-between items-center mt-1'):
                                        # Exclusive Primary Dispatch Checkbox implementation
                                        disp_radio = ui.checkbox('🌟 Primary Dispatch Admin', value=data.get('is_primary_dispatch', False)).classes('text-xs font-bold')

                                        def save_tech_config(t=tech, r=r_sel, e=e_inp, pi=pin_inp, v=v_sel, p1=p_min, p2=p_max, s1=s_min, s2=s_max, d_check=disp_radio):
                                            is_admin_flag = 1 if r.value in ['Admin', 'Both'] else 0
                                            is_primary_flag = 1 if (is_admin_flag and d_check.value) else 0
                                            v_val = None if v.value == 'None' else v.value
                                            
                                            conn = db.get_connection()
                                            cursor = conn.cursor()
                                            if is_primary_flag:
                                                # Enforce exclusivity in database
                                                cursor.execute("UPDATE technicians SET is_primary_dispatch = 0")

                                            cursor.execute('''
                                                UPDATE technicians 
                                                SET role=?, authorized_email=?, pin_code=?, assigned_vehicle=?, primary_min=?, primary_max=?, secondary_book_min=?, secondary_book_max=?, is_admin=?, is_primary_dispatch=?
                                                WHERE name=?
                                            ''', (r.value, e.value.strip(), pi.value.strip(), v_val, int(p1.value or 0), int(p2.value or 0), int(s1.value or 0), int(s2.value or 0), is_admin_flag, is_primary_flag, t))
                                            conn.commit()
                                            conn.close()
                                            refresh_tech_table()
                                            ui.notify(f'Updated configuration for {t}', type='positive')

                                        ui.button('💾 Save Changes', on_click=save_tech_config).props('dense outline color=primary').classes('text-xs')

                    refresh_tech_table()

                with ui.tab_panel(tab_stock):
                    categories = get_categories_list()

                    with ui.row().classes('w-full justify-between items-center mb-3'):
                        ui.label('Add New Inventory Item').classes('font-bold text-sm text-blue-900')
                        
                        def open_category_management_dialog():
                            with ui.dialog() as cat_dlg, ui.card().classes('w-96 p-4 gap-3 bg-white'):
                                ui.label('🛠️ Manage Inventory Categories').classes('font-bold text-blue-900 text-base border-b pb-1 w-full')
                                
                                new_cat_input = ui.input(label='New Category Name').classes('w-full').props('outlined dense')

                                def handle_add_category():
                                    val = (new_cat_input.value or '').strip()
                                    if val:
                                        cats = get_categories_list()
                                        if val not in cats:
                                            conn = db.get_connection()
                                            conn.cursor().execute("INSERT OR IGNORE INTO inventory_categories (name) VALUES (?)", (val,))
                                            conn.commit()
                                            conn.close()
                                            new_cat_input.value = ''
                                            cat_dlg.close()
                                            refresh_stock_table()
                                            ui.notify(f'Added category "{val}" successfully!', type='positive')
                                        else:
                                            ui.notify('Category already exists!', type='warning')

                                ui.button('➕ Add Category', on_click=handle_add_category).props('color=primary dense').classes('w-full text-xs font-bold')

                                ui.separator().classes('my-2')
                                ui.label('Existing Categories (Delete Option):').classes('font-bold text-xs text-gray-700')
                                
                                current_cats_list = [c for c in get_categories_list() if c != "All Categories"]
                                with ui.column().classes('w-full gap-1 max-h-48 overflow-y-auto'):
                                    for c_name in current_cats_list:
                                        with ui.row().classes('w-full justify-between items-center bg-slate-50 p-1 px-2 border rounded'):
                                            ui.label(c_name).classes('text-xs font-medium')
                                            def delete_cat(cat_to_del=c_name):
                                                conn = db.get_connection()
                                                conn.cursor().execute("DELETE FROM inventory_categories WHERE name = ?", (cat_to_del,))
                                                conn.commit()
                                                conn.close()
                                                cat_dlg.close()
                                                refresh_stock_table()
                                                ui.notify(f'Deleted category "{cat_to_del}"', type='warning')
                                            ui.button('🗑️', on_click=delete_cat).props('flat dense size=xs color=negative')

                                with ui.row().classes('w-full justify-end mt-2'):
                                    ui.button('Close', on_click=cat_dlg.close).props('flat dense')
                            cat_dlg.open()

                        ui.button('🍔 Category Menu', on_click=open_category_management_dialog).props('outline dense icon=menu color=primary').classes('text-xs font-bold')

                    with ui.card().classes('w-full p-4 bg-slate-100 border border-slate-300 mb-4 gap-2 shadow-sm'):
                        with ui.row().classes('w-full items-center gap-2'):
                            new_item_name = ui.input(label='Item Description').classes('w-4/12').props('outlined dense bg-white')
                            new_item_cat = ui.select(categories[1:], label='Category', value=categories[1] if len(categories)>1 else '').classes('w-3/12').props('outlined dense bg-white')
                            new_item_price = ui.number(label='Base Price (Ex)', value=0.0).classes('w-2/12').props('outlined dense bg-white')
                            new_item_sn = ui.checkbox('Requires S/N').classes('w-2/12 text-xs font-bold')
                        
                        def add_inventory_item():
                            name = (new_item_name.value or "").strip()
                            if name:
                                conn = db.get_connection()
                                conn.cursor().execute('''
                                    INSERT INTO inventory (item_name, price, requires_sn, category) 
                                    VALUES (?, ?, ?, ?)
                                ''', (name, float(new_item_price.value or 0), 1 if new_item_sn.value else 0, new_item_cat.value))
                                conn.commit()
                                conn.close()
                                refresh_stock_table()
                                new_item_name.value = ''
                                new_item_price.value = 0.0
                                new_item_sn.value = False
                                ui.notify(f'Saved "{name}" to Master Inventory Database!', type='positive')

                        ui.button('➕ Save Item to Catalog', on_click=add_inventory_item).props('dense').classes('bg-green-600 text-white font-bold text-xs')

                    ui.separator().classes('my-3')
                    with ui.row().classes('w-full justify-between items-center mb-2'):
                        ui.label('Existing Stock Catalog').classes('font-bold text-sm text-gray-800')
                        cat_filter = ui.select(get_categories_list(), value='All Categories', label='Filter Category', on_change=lambda _: refresh_stock_table()).classes('w-52').props('dense outlined bg-white')

                    stock_table_container = ui.column().classes('w-full gap-2')

                    def refresh_stock_table():
                        stock_table_container.clear()
                        current_cats = get_categories_list()
                        cat_filter.set_options(current_cats)
                        selected_cat = cat_filter.value
                        inventory_data = db.get_inventory_db()
                        
                        with stock_table_container:
                            with ui.row().classes('w-full text-xs font-bold bg-slate-200 p-2 rounded gap-2'):
                                ui.label('Item Description').classes('w-4/12')
                                ui.label('Category').classes('w-3/12')
                                ui.label('Price (Ex)').classes('w-2/12')
                                ui.label('S/N Req').classes('w-1/12')
                                ui.label('Actions').classes('w-2/12 text-center')

                            for item, data in inventory_data.items():
                                if selected_cat != "All Categories" and data.get('category') != selected_cat:
                                    continue

                                with ui.row().classes('w-full items-center border-b pb-1 gap-2 bg-white p-1 rounded'):
                                    ui.label(item).classes('w-4/12 font-medium text-xs')
                                    cat_select = ui.select(current_cats[1:], value=data.get('category', current_cats[1] if len(current_cats)>1 else '')).classes('w-3/12').props('dense outlined')
                                    price_input = ui.number(value=data['price']).classes('w-2/12').props('outlined dense')
                                    sn_check = ui.checkbox(value=data['requires_sn']).classes('w-1/12')

                                    def save_changes(i=item, p=price_input, s=sn_check, c=cat_select):
                                        conn = db.get_connection()
                                        conn.cursor().execute('''
                                            UPDATE inventory SET price=?, requires_sn=?, category=? WHERE item_name=?
                                        ''', (float(p.value or 0), 1 if s.value else 0, c.value, i))
                                        conn.commit()
                                        conn.close()
                                        ui.notify(f'Updated "{i}" in Database', type='info')

                                    def delete_inventory_item(i=item):
                                        with ui.dialog() as del_item_dlg, ui.card().classes('w-80 p-4 gap-3 bg-white'):
                                            ui.label(f'⚠️ Delete Stock Item?').classes('font-bold text-red-600 text-base')
                                            ui.label(f'Are you sure you want to remove "{i}" from master inventory?').classes('text-xs text-gray-700')
                                            
                                            def confirm_del():
                                                conn = db.get_connection()
                                                conn.cursor().execute("DELETE FROM inventory WHERE item_name = ?", (i,))
                                                conn.commit()
                                                conn.close()
                                                del_item_dlg.close()
                                                refresh_stock_table()
                                                ui.notify(f'Removed item "{i}" from catalog.', type='warning')

                                            with ui.row().classes('w-full justify-end gap-2 mt-2'):
                                                ui.button('Cancel', on_click=del_item_dlg.close).props('flat dense')
                                                ui.button('YES, DELETE', on_click=confirm_del).props('color=negative dense font-bold')
                                        del_item_dlg.open()

                                    with ui.row().classes('w-2/12 justify-center gap-1'):
                                        ui.button('💾', on_click=save_changes).props('flat dense color=primary')
                                        ui.button('❌', on_click=delete_inventory_item).props('flat dense color=negative')

                    refresh_stock_table()

                with ui.tab_panel(tab_clients):
                    with ui.row().classes('w-full justify-between items-center mb-2'):
                        ui.label('Register New Store / Client, Franchise & Emails').classes('font-bold text-sm text-blue-900')
                        
                        # Deleted Stores Audit Log Dialog Button
                        def open_deleted_audit_dialog():
                            with ui.dialog() as audit_dlg, ui.card().classes('w-[600px] p-5 gap-3 bg-white'):
                                ui.label('🗑️ Deleted Stores Audit Log').classes('font-bold text-red-700 text-base border-b pb-2 w-full')
                                
                                conn = db.get_connection()
                                cursor = conn.cursor()
                                cursor.execute("CREATE TABLE IF NOT EXISTS deleted_clients_log (id INTEGER PRIMARY KEY AUTOINCREMENT, store_name TEXT, reason TEXT, deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                                cursor.execute("SELECT store_name, reason, deleted_at FROM deleted_clients_log ORDER BY id DESC")
                                logs = cursor.fetchall()
                                conn.close()

                                if logs:
                                    with ui.column().classes('w-full gap-2 max-h-96 overflow-y-auto'):
                                        for l in logs:
                                            with ui.card().classes('w-full p-3 bg-slate-50 border shadow-none gap-1'):
                                                with ui.row().classes('w-full justify-between items-center'):
                                                    ui.label(f"Store: {l['store_name']}").classes('font-bold text-blue-900 text-xs')
                                                    ui.label(f"Deleted: {l['deleted_at']}").classes('text-[10px] text-gray-500')
                                                ui.label(f"Reason: {l['reason']}").classes('text-xs text-gray-800 italic')
                                else:
                                    ui.label('No deleted stores logged yet.').classes('text-xs text-gray-400 italic py-4')

                                with ui.row().classes('w-full justify-end mt-2'):
                                    ui.button('Close', on_click=audit_dlg.close).props('flat dense')
                            audit_dlg.open()

                        ui.button('📋 View Deleted Stores Log', on_click=open_deleted_audit_dialog).props('outline dense color=negative icon=history').classes('text-xs font-bold')

                    with ui.card().classes('w-full p-4 bg-slate-100 border border-slate-300 mb-4 gap-2 shadow-sm'):
                        with ui.row().classes('w-full items-center gap-2'):
                            new_client_name = ui.input(label='Store / Client Name').classes('w-4/12').props('outlined dense bg-white')
                            new_franchise_name = ui.input(label='Franchise Group (Leave blank if Independent)').classes('w-3/12').props('outlined dense bg-white')
                            first_contact = ui.input(label='Primary Contact Name').classes('w-2/12').props('outlined dense bg-white')
                            new_store_email = ui.input(label='Store Email(s)').classes('w-3/12').props('outlined dense bg-white')

                        def add_client_store():
                            store = (new_client_name.value or "").strip()
                            franchise = (new_franchise_name.value or "").strip()
                            contact = (first_contact.value or "").strip()
                            s_email = (new_store_email.value or "").strip()
                            if store:
                                conn = db.get_connection()
                                conn.cursor().execute("INSERT INTO clients (store_name, contacts, store_email, franchise_group) VALUES (?, ?, ?, ?)", 
                                                        (store, db.json.dumps([contact] if contact else []), s_email, franchise))
                                conn.commit()
                                conn.close()
                                refresh_client_table()
                                new_client_name.value = ''
                                new_franchise_name.value = ''
                                first_contact.value = ''
                                new_store_email.value = ''
                                ui.notify(f'Saved store "{store}"!', type='positive')

                        ui.button('➕ Add Store', on_click=add_client_store).props('dense').classes('bg-blue-800 text-white font-bold text-xs')

                    ui.separator().classes('my-3')

                    # Live Search Bar with smart franchise drilling
                    store_search_input = ui.input(label='🔍 Search Stores / Franchises...', placeholder='Type store name, franchise, email, or contact...').classes('w-full mb-3').props('outlined dense bg-white clearable')
                    store_search_input.on('update:model-value', lambda _: refresh_client_table())

                    client_table_container = ui.column().classes('w-full gap-3')

                    def refresh_client_table():
                        client_table_container.clear()
                        clients_data = db.get_all_clients()
                        search_query = (store_search_input.value or "").strip().lower()

                        franchise_groups = {}
                        independent_stores = {}

                        for store, store_info in clients_data.items():
                            f_group = (store_info.get("franchise_group") or "").strip()
                            
                            # Filter based on search input
                            if search_query:
                                match_store = search_query in store.lower()
                                match_franchise = search_query in f_group.lower()
                                match_email = any(search_query in e.lower() for e in store_info.get("email", ""))
                                match_contact = any(search_query in c.lower() for c in store_info.get("contacts", []))
                                if not (match_store or match_franchise or match_email or match_contact):
                                    continue

                            if not f_group or f_group.lower() in ["none", "independent", "ungrouped"]:
                                independent_stores[store] = store_info
                            else:
                                franchise_groups.setdefault(f_group, {})[store] = store_info

                        with client_table_container:
                            # 1. Render actual Franchises grouped together
                            for f_name, stores_dict in sorted(franchise_groups.items()):
                                if stores_dict:
                                    with ui.expansion(f"🏢 {f_name} ({len(stores_dict)} Stores)", icon='hub').classes('w-full bg-slate-50 border rounded font-bold text-blue-900 my-1') as exp:
                                        # Auto-expand the franchise group if user search matches the franchise name or any store inside it
                                        if search_query and (search_query in f_name.lower() or any(search_query in s.lower() for s in stores_dict)):
                                            exp.value = True
                                        render_store_cards(stores_dict)

                            # 2. Render Independent stores individually
                            if independent_stores:
                                for store, store_info in sorted(independent_stores.items()):
                                    ind_dict = {store: store_info}
                                    render_store_cards(ind_dict)

                    def render_store_cards(stores_dict):
                        for idx, (store, store_info) in enumerate(stores_dict.items()):
                            contacts = store_info["contacts"]
                            s_emails_raw = store_info["email"]
                            email_list = [e.strip() for e in s_emails_raw.replace(';', ',').split(',') if e.strip()]
                            current_group = store_info.get("franchise_group", "")

                            bg_class = 'bg-slate-50' if idx % 2 == 0 else 'bg-white'

                            with ui.card().classes(f'w-full p-4 border border-slate-300 {bg_class} shadow-sm gap-3 my-2'):
                                with ui.row().classes('w-full justify-between items-center border-b pb-2'):
                                    with ui.row().classes('items-center gap-2'):
                                        ui.label(store).classes('font-bold text-base text-blue-900')
                                        
                                        fran_input = ui.input(value=current_group).classes('w-44').props('dense outlined label="Franchise Group"')
                                        def update_fran(s=store, fi=fran_input):
                                            val = fi.value.strip()
                                            db.update_client_franchise(s, val)
                                            ui.notify(f'Updated group for {s}', type='info')
                                            refresh_client_table()
                                        ui.button('Update Group', on_click=update_fran).props('dense outline size=xs').classes('text-[10px]')

                                    def confirm_delete_client(s_name=store):
                                        with ui.dialog() as del_c_dlg, ui.card().classes('w-96 p-4 gap-3 bg-white'):
                                            ui.label(f'⚠️ Delete Client / Store?').classes('font-bold text-red-600 text-base')
                                            ui.label(f'To confirm deletion of "{s_name}", please type the store name below and provide a reason:').classes('text-xs text-gray-700')
                                            
                                            confirm_name_input = ui.input(label='Retype Store Name').classes('w-full').props('outlined dense')
                                            reason_input = ui.textarea(label='Reason for Deletion (Required)').classes('w-full').props('outlined rows=2')

                                            def execute_client_delete():
                                                entered_name = (confirm_name_input.value or '').strip()
                                                reason_val = (reason_input.value or '').strip()

                                                if entered_name != s_name:
                                                    ui.notify('Store name does not match!', type='negative')
                                                    return
                                                if not reason_val:
                                                    ui.notify('Please provide a mandatory reason for deletion!', type='negative')
                                                    return

                                                conn = db.get_connection()
                                                cursor = conn.cursor()
                                                cursor.execute("CREATE TABLE IF NOT EXISTS deleted_clients_log (id INTEGER PRIMARY KEY AUTOINCREMENT, store_name TEXT, reason TEXT, deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
                                                cursor.execute("INSERT INTO deleted_clients_log (store_name, reason) VALUES (?, ?)", (s_name, reason_val))
                                                cursor.execute("DELETE FROM clients WHERE store_name = ?", (s_name,))
                                                conn.commit()
                                                conn.close()

                                                del_c_dlg.close()
                                                refresh_client_table()
                                                ui.notify(f'Successfully deleted client "{s_name}". Reason logged.', type='warning')

                                            with ui.row().classes('w-full justify-end gap-2 mt-2'):
                                                ui.button('Cancel', on_click=del_c_dlg.close).props('flat dense')
                                                ui.button('CONFIRM DELETE', on_click=execute_client_delete).props('color=negative dense font-bold')
                                        del_c_dlg.open()

                                    ui.button('🗑️ Delete Store', on_click=confirm_delete_client).props('dense outline size=xs color=negative')

                                # Email Management
                                ui.label('Store Dispatch Email Addresses (First badge is Primary):').classes('text-xs font-bold text-gray-700')
                                with ui.row().classes('w-full gap-1 items-center flex-wrap'):
                                    if email_list:
                                        for e_idx, em in enumerate(email_list):
                                            is_primary = (e_idx == 0)
                                            badge_color = 'green-3' if is_primary else 'blue-2'
                                            badge_text_color = 'text-green-900 font-bold' if is_primary else 'text-blue-900'
                                            
                                            with ui.badge(em, color=badge_color).classes(f'{badge_text_color} text-xs px-2 py-1 items-center gap-1'):
                                                if is_primary:
                                                    ui.label('⭐ Primary').classes('text-[9px] font-black mr-1')
                                                else:
                                                    def make_primary(s=store, target_em=em, current_list=email_list):
                                                        current_list.remove(target_em)
                                                        current_list.insert(0, target_em)
                                                        db.update_store_email_list(s, current_list)
                                                        refresh_client_table()
                                                        ui.notify(f'Set "{target_em}" as Primary Email!', type='positive')
                                                    ui.button('Make Primary', on_click=make_primary).props('flat dense size=xs').classes('text-[9px] underline')

                                            def remove_email(s=store, target_em=em, current_list=email_list):
                                                if len(current_list) > 1:
                                                    current_list.remove(target_em)
                                                    db.update_store_email_list(s, current_list)
                                                    refresh_client_table()
                                                    ui.notify(f'Removed email "{target_em}"', type='warning')
                                                else:
                                                    ui.notify('Store must retain at least one dispatch email address.', type='warning')

                                            ui.button('×', on_click=remove_email).props('flat dense size=xs color=negative')
                                    else:
                                        ui.label('No email addresses recorded.').classes('text-xs text-gray-400 italic')

                                with ui.row().classes('w-full items-center gap-2 mt-1'):
                                    add_email_input = ui.input(placeholder='+ Add another email address...').classes('w-8/12').props('dense outlined bg-white')
                                    
                                    def add_email_to_store(s=store, inp=add_email_input, current_list=email_list):
                                        val = (inp.value or '').strip()
                                        if val:
                                            if val not in current_list:
                                                current_list.append(val)
                                                db.update_store_email_list(s, current_list)
                                                refresh_client_table()
                                                ui.notify(f'Added email "{val}"!', type='positive')
                                            else:
                                                ui.notify('Email already exists for this store.', type='warning')

                                    ui.button('Add Email', on_click=add_email_to_store).props('dense outline').classes('w-3/12 text-xs')

                                ui.separator().classes('my-1')

                                # Contacts Management
                                with ui.row().classes('w-full gap-1 items-center flex-wrap'):
                                    ui.label('Contacts:').classes('text-xs font-bold text-gray-600 mr-1')
                                    if contacts:
                                        for c in list(contacts):
                                            def remove_c(s=store, name=c):
                                                contacts.remove(name)
                                                conn = db.get_connection()
                                                conn.cursor().execute("UPDATE clients SET contacts=? WHERE store_name=?", (db.json.dumps(contacts), s))
                                                conn.commit()
                                                conn.close()
                                                refresh_client_table()
                                                ui.notify(f'Removed "{name}"', type='warning')
                                                
                                            with ui.badge(c, color='slate-2').classes('text-slate-900 text-xs px-2 py-1 items-center gap-1'):
                                                ui.button('×', on_click=remove_c).props('flat dense size=xs color=negative')
                                    else:
                                        ui.label('No contacts listed.').classes('text-xs text-gray-400 italic')

                                with ui.row().classes('w-full items-center gap-2 mt-1'):
                                    add_sec_input = ui.input(placeholder='+ Add Contact Name...').classes('w-8/12').props('dense outlined bg-white')
                                    
                                    def add_secondary(s=store, inp=add_sec_input):
                                        new_name = (inp.value or "").strip()
                                        if new_name:
                                            db.add_client_contact(s, new_name)
                                            refresh_client_table()
                                            ui.notify(f'Added contact "{new_name}"!', type='positive')

                                    ui.button('Add Contact', on_click=add_secondary).props('dense outline').classes('w-3/12 text-xs')

                                # Linked Job Cards History accordion
                                with ui.expansion('📋 Linked Job Cards History', icon='receipt_long').classes('w-full bg-slate-50 border rounded text-xs mt-2'):
                                    all_jc_history = db.get_job_card_history()
                                    store_jobs = [j for j in all_jc_history if j.get('client') == store]
                                    
                                    if store_jobs:
                                        with ui.column().classes('w-full gap-1 p-1'):
                                            for job in store_jobs:
                                                with ui.row().classes('w-full justify-between items-center border-b py-1 px-2 bg-white rounded'):
                                                    with ui.column().classes('gap-0'):
                                                        ui.label(f"{job['jc_no']} — Tech: {job.get('tech', 'N/A')}").classes('font-bold text-blue-900')
                                                        ui.label(f"Date: {job['date_str']} | Total: R{job['total']:.2f}").classes('text-[10px] text-gray-500')
                                                    
                                                    def print_client_job(rec=job):
                                                        pdf_gen.generate_jobcard_pdf(rec, f"{rec['jc_no']}.pdf")
                                                        ui.download(f"{rec['jc_no']}.pdf")
                                                        ui.notify(f"Downloaded {rec['jc_no']}.pdf", type='positive')

                                                    ui.button('🖨️ PDF', on_click=print_client_job).props('dense outline size=xs color=primary')
                                    else:
                                        ui.label('No job cards linked to this store yet.').classes('text-xs text-gray-400 italic p-2')

                    refresh_client_table()