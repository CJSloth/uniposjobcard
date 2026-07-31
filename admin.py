from nicegui import ui
import database as db
import json

ADMIN_PASSWORD = "34959"

categories = [
    "All Categories",
    "Hardware / Terminals",
    "Monitors & Displays",
    "Scanners & Peripherals",
    "Accessories & Cables",
    "Services & Installs"
]

def create_admin_page():
    authenticated = {'status': False}

    with ui.dialog() as auth_dialog, ui.card().classes('w-80 p-4 items-center gap-2'):
        ui.label('🔒 Admin Password Required').classes('font-bold text-blue-900 text-sm')
        pwd_input = ui.input(placeholder='Enter Admin Password', password=True).classes('w-full').props('outlined dense')
        
        def verify_pwd():
            if pwd_input.value == ADMIN_PASSWORD:
                authenticated['status'] = True
                auth_dialog.close()
                admin_content_card.set_visibility(True)
                ui.notify('Access Granted!', type='positive')
            else:
                ui.notify('Incorrect Password!', type='negative')
                pwd_input.value = ''

        pwd_input.on('keydown.enter', verify_pwd)
        ui.button('UNLOCK PORTAL', on_click=verify_pwd).props('color=primary dense').classes('w-full mt-2 font-bold')

    auth_dialog.open()

    with ui.card().classes('w-full max-w-5xl mx-auto p-4 my-4 bg-white shadow-xl rounded-lg text-sm') as admin_content_card:
        admin_content_card.set_visibility(False)

        # Header
        with ui.row().classes('w-full justify-between items-center border-b pb-3 mb-4'):
            with ui.column().classes('gap-0'):
                ui.label('UNIPOS RETAIL SOLUTIONS').classes('text-xl font-black text-blue-900')
                ui.label('System Administration & Dispatch Portal').classes('text-xs text-gray-500 font-bold')
            
            ui.button('👈 Back to Job Card', on_click=lambda: ui.navigate.to('/')).props('outline dense icon=arrow_back')

        # Navigation Tabs
        with ui.tabs().classes('w-full') as tabs:
            tab_techs = ui.tab('Field Technicians & Fleet', icon='engineering')
            tab_stock = ui.tab('Stock & Pricing Master', icon='inventory_2')
            tab_clients = ui.tab('Clients & Contacts', icon='storefront')

        with ui.tab_panels(tabs, value=tab_techs).classes('w-full pt-4'):
            
            # ------------------------------------------------------------------
            # TAB 1: FIELD TECHNICIANS, FLEET & AUTOMATIC YEAR/MONTH HISTORY
            # ------------------------------------------------------------------
            with ui.tab_panel(tab_techs):
                
                # Fleet Management Card
                with ui.card().classes('w-full p-3 bg-blue-50 border border-blue-200 mb-4 gap-2 shadow-none'):
                    ui.label('🚗 Fleet Vehicle Management').classes('font-bold text-sm text-blue-900')
                    
                    with ui.row().classes('w-full items-center gap-2'):
                        new_veh_input = ui.input(placeholder='e.g. CA123456 or BFN999FS').classes('w-6/12').props('outlined dense bg-white')
                        
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

                        ui.button('➕ Add Fleet Vehicle', on_click=add_new_vehicle).props('dense color=primary').classes('w-4/12 text-xs font-bold')

                    fleet_badge_container = ui.row().classes('w-full gap-1 items-center mt-1')
                    def refresh_fleet_badges():
                        fleet_badge_container.clear()
                        vehs = db.get_vehicles()
                        with fleet_badge_container:
                            ui.label('Active Fleet:').classes('text-xs font-bold text-gray-700 mr-1')
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

                ui.separator().classes('my-2')

                # Technician Registration
                ui.label('Register New Technician').classes('font-bold text-sm text-blue-900 mb-2')
                
                with ui.card().classes('w-full p-3 bg-gray-50 border mb-4 gap-2 shadow-none'):
                    with ui.row().classes('w-full items-center gap-2'):
                        vehs_list = db.get_vehicles()
                        t_name = ui.input(label='Technician Name').classes('w-3/12').props('outlined dense')
                        t_veh = ui.select(vehs_list, label='Assigned Vehicle', value=vehs_list[0] if vehs_list else '').classes('w-2/12').props('outlined dense')
                        t_min = ui.number(label='JC Min', value=4000).classes('w-2/12').props('outlined dense')
                        t_max = ui.number(label='JC Max', value=4999).classes('w-2/12').props('outlined dense')
                        t_sec_min = ui.number(label='Paper Book Min', value=0).classes('w-2/12').props('outlined dense')

                    def add_tech():
                        name = (t_name.value or "").strip()
                        techs = db.get_technicians_db()
                        if name and name not in techs:
                            conn = db.get_connection()
                            conn.cursor().execute('''
                                INSERT INTO technicians 
                                (name, assigned_vehicle, primary_min, primary_max, current_jc, secondary_book_min, secondary_book_max)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                name, t_veh.value, int(t_min.value or 0), int(t_max.value or 0), 
                                int(t_min.value or 0), int(t_sec_min.value) if t_sec_min.value else None,
                                int(t_sec_min.value + 99) if t_sec_min.value else None
                            ))
                            conn.commit()
                            conn.close()
                            refresh_tech_table()
                            t_name.value = ''
                            ui.notify(f'Saved Technician "{name}" to Database!', type='positive')

                    ui.button('➕ Add Technician', on_click=add_tech).props('dense').classes('bg-blue-800 text-white font-bold text-xs')

                ui.separator().classes('my-2')
                ui.label('Active Technicians, Vehicle Assignments & Ranges').classes('font-bold text-sm text-gray-800 mb-2')

                tech_table_container = ui.column().classes('w-full gap-2')

                def refresh_tech_table():
                    tech_table_container.clear()
                    refresh_fleet_badges()
                    techs = db.get_technicians_db()
                    vehs_list = db.get_vehicles()

                    with tech_table_container:
                        for tech, data in techs.items():
                            with ui.card().classes('w-full p-3 border bg-gray-50 shadow-none gap-2'):
                                with ui.row().classes('w-full justify-between items-center border-b pb-2'):
                                    ui.label(f"👤 {tech}").classes('font-bold text-base text-blue-900')
                                    ui.badge(f"Current JC: JC-{data['current_jc']}", color='blue-9').classes('text-xs px-2 py-1')

                                with ui.grid(columns=3).classes('w-full gap-2'):
                                    v_sel = ui.select(vehs_list, label='Assigned Vehicle:', value=data['assigned_vehicle']).classes('w-full').props('outlined dense')
                                    p_min = ui.number(label='JC Min:', value=data['primary_min']).classes('w-full').props('outlined dense')
                                    p_max = ui.number(label='JC Max:', value=data['primary_max']).classes('w-full').props('outlined dense')

                                with ui.row().classes('w-full items-center gap-2 bg-blue-50 p-2 rounded border border-blue-100'):
                                    ui.label('📖 Paper Backup Range:').classes('font-bold text-xs text-blue-900 w-3/12')
                                    sec_min = ui.number(label='Book Start', value=data.get('secondary_book_min') or 0).classes('w-4/12').props('outlined dense bg-white')
                                    sec_max = ui.number(label='Book End', value=data.get('secondary_book_max') or 0).classes('w-4/12').props('outlined dense bg-white')

                                with ui.row().classes('w-full justify-between items-center mt-1'):
                                    def save_tech_config(t=tech, v=v_sel, p1=p_min, p2=p_max, s1=sec_min, s2=sec_max):
                                        conn = db.get_connection()
                                        conn.cursor().execute('''
                                            UPDATE technicians 
                                            SET assigned_vehicle=?, primary_min=?, primary_max=?, secondary_book_min=?, secondary_book_max=?
                                            WHERE name=?
                                        ''', (v.value, int(p1.value or 0), int(p2.value or 0), int(s1.value) if s1.value else None, int(s2.value) if s2.value else None, t))
                                        conn.commit()
                                        conn.close()
                                        ui.notify(f'Updated configuration for {t}', type='positive')

                                    ui.button('💾 Save Changes', on_click=save_tech_config).props('dense outline color=primary').classes('text-xs')

                                    # FULL INSPECTION DIALOG (WITH YEAR & MONTH FILTERS)
                                    def open_history(t=tech):
                                        with ui.dialog() as hist_dialog, ui.card().classes('w-full max-w-3xl p-4'):
                                            ui.label(f'📜 Automatic History Inspector - {t}').classes('font-bold text-base text-blue-900 border-b pb-2 w-full')
                                            
                                            all_history = db.get_job_card_history()
                                            tech_jobs = [j for j in all_history if j['tech'] == t]
                                            
                                            if tech_jobs:
                                                year_month_map = {}
                                                for j in tech_jobs:
                                                    d_str = j.get('date_str', '2026-01-01')
                                                    y_key = d_str[:4]
                                                    m_key = d_str[:7]
                                                    year_month_map.setdefault(y_key, {}).setdefault(m_key, []).append(j)

                                                all_years = list(year_month_map.keys())
                                                sel_year = all_years[0]
                                                all_months = list(year_month_map[sel_year].keys())
                                                sel_month = all_months[0]

                                                with ui.row().classes('w-full items-center justify-between bg-blue-50 p-2 rounded my-2 gap-2'):
                                                    with ui.row().classes('items-center gap-2'):
                                                        ui.label('Year:').classes('font-bold text-xs text-blue-900')
                                                        y_select = ui.select(all_years, value=sel_year).classes('w-28').props('dense outlined bg-white')
                                                    
                                                    with ui.row().classes('items-center gap-2'):
                                                        ui.label('Billing Month:').classes('font-bold text-xs text-blue-900')
                                                        m_select = ui.select(all_months, value=sel_month).classes('w-36').props('dense outlined bg-white')

                                                list_container = ui.column().classes('w-full gap-2 my-2 max-h-[350px] overflow-y-auto')

                                                def render_jobs(y_val, m_val):
                                                    list_container.clear()
                                                    jobs = year_month_map.get(y_val, {}).get(m_val, [])
                                                    
                                                    with list_container:
                                                        with ui.row().classes('w-full text-xs font-bold bg-gray-200 p-2 rounded gap-2'):
                                                            ui.label('JC No').classes('w-2/12')
                                                            ui.label('Date').classes('w-2/12')
                                                            ui.label('Client Store').classes('w-4/12')
                                                            ui.label('Grand Total').classes('w-2/12 text-right')
                                                            ui.label('Action').classes('w-1/12 text-center')

                                                        if jobs:
                                                            for job in jobs:
                                                                with ui.row().classes('w-full items-center border-b pb-1 gap-2 text-xs'):
                                                                    ui.label(job['jc_no']).classes('w-2/12 font-bold text-blue-900')
                                                                    ui.label(job['date_str']).classes('w-2/12 text-gray-600')
                                                                    ui.label(job.get('client', 'N/A')).classes('w-4/12 font-medium truncate')
                                                                    ui.label(f"R{job['total']:.2f}").classes('w-2/12 text-right font-bold text-green-700')

                                                                    # SINGLE FULL JOBCARD POPUP
                                                                    def inspect_single(j=job):
                                                                        with ui.dialog() as single_dlg, ui.card().classes('w-full max-w-2xl p-4 gap-2 bg-white'):
                                                                            with ui.row().classes('w-full justify-between items-center border-b pb-2'):
                                                                                with ui.column().classes('gap-0'):
                                                                                    ui.label('UNIPOS RETAIL SOLUTIONS').classes('text-base font-black text-blue-900')
                                                                                    ui.label('FULL HISTORICAL JOB CARD').classes('text-[10px] font-bold text-gray-500')
                                                                                with ui.column().classes('items-end gap-0'):
                                                                                    ui.label(f"Jobcard No: {j['jc_no']}").classes('font-black text-red-600 text-sm')
                                                                                    ui.label(f"Date: {j['date_str']}").classes('text-xs text-gray-600')

                                                                            with ui.grid(columns=2).classes('w-full gap-1 text-xs bg-gray-50 p-2 border rounded'):
                                                                                ui.label(f"To (Client): {j.get('client', 'N/A')}").classes('font-semibold')
                                                                                ui.label(f"Called By: {j.get('called_by', 'N/A')}")
                                                                                ui.label(f"Technician: {j.get('tech', 'N/A')}")
                                                                                ui.label(f"Vehicle Reg: {j.get('vehicle', 'N/A')}")

                                                                            with ui.column().classes('w-full gap-1 text-xs my-1'):
                                                                                ui.label(f"Details of Fault: {j.get('fault', 'None listed')}").classes('font-bold text-gray-800')
                                                                                ui.label(f"Actions Taken Log:\n{j.get('actions', 'None listed')}").classes('text-gray-700 whitespace-pre-line bg-gray-50 p-2 border rounded w-full')

                                                                            ui.label("Stock / Spares / Line Items Used:").classes('font-bold text-xs text-blue-900 mt-1')
                                                                            with ui.column().classes('w-full gap-1 bg-gray-100 p-2 border rounded text-xs'):
                                                                                try:
                                                                                    items = json.loads(j.get('items_json', '[]'))
                                                                                    if items:
                                                                                        for it in items:
                                                                                            serials = ", ".join(it.get('serials', [])) if it.get('serials') else "No S/N"
                                                                                            price_val = it.get('price') or 0.0
                                                                                            ui.label(f"• {it.get('item')} | Qty: {it.get('qty')} | Price: R{price_val:.2f} | S/N: [{serials}]").classes('font-mono')
                                                                                    else:
                                                                                        ui.label("No stock items recorded.").classes('italic text-gray-500')
                                                                                except Exception:
                                                                                    ui.label("No stock items recorded.").classes('italic text-gray-500')

                                                                            with ui.grid(columns=2).classes('w-full gap-2 border-t pt-2 my-1 text-xs'):
                                                                                with ui.column().classes('gap-1'):
                                                                                    ui.label(f"Time Started: {j.get('time_start', 'N/A')} | Time Completed: {j.get('time_end', 'N/A')}")
                                                                                    ui.label(f"Customer Comments: {j.get('customer_comments', 'None')}").classes('italic text-gray-600')
                                                                                    ui.label(f"Payment Method: {j.get('payment_method', 'N/A')}").classes('font-semibold text-blue-900')

                                                                                with ui.card().classes('w-full p-2 bg-gray-50 border gap-1 shadow-none'):
                                                                                    ui.label("Calculations Breakdown:").classes('font-bold border-b pb-1')
                                                                                    
                                                                                    hrs = j.get('billable_hrs') if j.get('billable_hrs') is not None else 1.0
                                                                                    hr_rate = j.get('hourly_rate') if j.get('hourly_rate') is not None else 650.0
                                                                                    km = j.get('km_driven') if j.get('km_driven') is not None else 0.0
                                                                                    r_km = j.get('rate_per_km') if j.get('rate_per_km') is not None else 7.50
                                                                                    c_fee = j.get('callout_fee') if j.get('callout_fee') is not None else 450.0
                                                                                    
                                                                                    sub_tot = j.get('subtotal') if j.get('subtotal') is not None else 0.0
                                                                                    vat_val = j.get('vat') if j.get('vat') is not None else 0.0
                                                                                    tot_val = j.get('total') if j.get('total') is not None else 0.0

                                                                                    ui.label(f"Billable Hours: {hrs} hrs @ R{hr_rate:.2f}/hr")
                                                                                    ui.label(f"KM Travelled: {km} km @ R{r_km:.2f}/km = R{km * r_km:.2f}")
                                                                                    ui.label(f"Call-Out Fee: R{c_fee:.2f}")
                                                                                    
                                                                                    ui.separator()
                                                                                    ui.label(f"Subtotal (Ex): R{sub_tot:.2f}").classes('font-bold')
                                                                                    ui.label(f"15% VAT: R{vat_val:.2f}").classes('text-gray-600')
                                                                                    ui.label(f"Grand Total (Inc): R{tot_val:.2f}").classes('font-black text-green-800 text-sm')

                                                                            ui.button('CLOSE FULL JOBCARD', on_click=single_dlg.close).props('color=primary dense').classes('w-full mt-2 font-bold')
                                                                        single_dlg.open()

                                                                    with ui.row().classes('w-1/12 justify-center'):
                                                                        ui.button('🔍', on_click=inspect_single).props('flat dense color=primary')
                                                        else:
                                                            ui.label('No records for this selected month.').classes('text-xs text-gray-400 italic my-2')

                                                def on_year_change(e):
                                                    y_val = e.value
                                                    avail_m = list(year_month_map.get(y_val, {}).keys())
                                                    m_select.set_options(avail_m)
                                                    if avail_m:
                                                        m_select.value = avail_m[0]
                                                        render_jobs(y_val, avail_m[0])

                                                y_select.on_value_change(on_year_change)
                                                m_select.on_value_change(lambda e: render_jobs(y_select.value, e.value))
                                                render_jobs(sel_year, sel_month)

                                            else:
                                                ui.label('No past job cards found in database for this technician.').classes('text-xs text-gray-400 italic my-2')

                                            ui.button('Close Inspector', on_click=hist_dialog.close).props('color=primary dense').classes('w-full mt-2 font-bold')
                                        hist_dialog.open()

                                    ui.button('🔍 Inspect Full Job Cards', on_click=open_history).props('dense flat icon=visibility').classes('text-xs text-gray-700')

                refresh_tech_table()

            # ------------------------------------------------------------------
            # TAB 2: STOCK & CATEGORIES
            # ------------------------------------------------------------------
            with ui.tab_panel(tab_stock):
                ui.label('Add New Inventory Item').classes('font-bold text-sm text-blue-900 mb-2')
                
                with ui.card().classes('w-full p-3 bg-gray-50 border mb-4 gap-2 shadow-none'):
                    with ui.row().classes('w-full items-center gap-2'):
                        new_item_name = ui.input(label='Item Description').classes('w-4/12').props('outlined dense')
                        new_item_cat = ui.select(categories[1:], label='Category', value=categories[1]).classes('w-3/12').props('outlined dense')
                        new_item_price = ui.number(label='Base Price (Ex)', value=0.0).classes('w-2/12').props('outlined dense')
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

                ui.separator().classes('my-2')
                
                with ui.row().classes('w-full justify-between items-center mb-2'):
                    ui.label('Existing Stock Catalog').classes('font-bold text-sm text-gray-800')
                    cat_filter = ui.select(categories, value='All Categories', label='Filter Category', on_change=lambda _: refresh_stock_table()).classes('w-52').props('dense outlined')

                stock_table_container = ui.column().classes('w-full gap-1')

                def refresh_stock_table():
                    stock_table_container.clear()
                    selected_cat = cat_filter.value
                    inventory_data = db.get_inventory_db()
                    
                    with stock_table_container:
                        with ui.row().classes('w-full text-xs font-bold bg-gray-200 p-2 rounded gap-2'):
                            ui.label('Item Description').classes('w-4/12')
                            ui.label('Category').classes('w-3/12')
                            ui.label('Price (Ex)').classes('w-2/12')
                            ui.label('S/N Req').classes('w-1/12')
                            ui.label('Action').classes('w-1/12 text-center')

                        for item, data in inventory_data.items():
                            if selected_cat != "All Categories" and data.get('category') != selected_cat:
                                continue

                            with ui.row().classes('w-full items-center border-b pb-1 gap-2'):
                                ui.label(item).classes('w-4/12 font-medium text-xs')
                                cat_select = ui.select(categories[1:], value=data.get('category', categories[1])).classes('w-3/12').props('dense outlined')
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

                                with ui.row().classes('w-1/12 justify-center'):
                                    ui.button('💾', on_click=save_changes).props('flat dense color=primary')

                refresh_stock_table()

            # ------------------------------------------------------------------
            # TAB 3: CLIENTS & CONTACTS
            # ------------------------------------------------------------------
            with ui.tab_panel(tab_clients):
                ui.label('Register New Store / Client').classes('font-bold text-sm text-blue-900 mb-2')
                
                with ui.card().classes('w-full p-3 bg-gray-50 border mb-4 gap-2 shadow-none'):
                    with ui.row().classes('w-full items-center gap-2'):
                        new_client_name = ui.input(label='Store / Client Name').classes('w-6/12').props('outlined dense')
                        first_contact = ui.input(label='Primary Contact Name').classes('w-5/12').props('outlined dense')

                    def add_client_store():
                        store = (new_client_name.value or "").strip()
                        contact = (first_contact.value or "").strip()
                        if store:
                            conn = db.get_connection()
                            conn.cursor().execute("INSERT INTO clients (store_name, contacts) VALUES (?, ?)", 
                                                (store, db.json.dumps([contact] if contact else [])))
                            conn.commit()
                            conn.close()
                            refresh_client_table()
                            new_client_name.value = ''
                            first_contact.value = ''
                            ui.notify(f'Saved store "{store}" to database!', type='positive')

                    ui.button('➕ Add Store', on_click=add_client_store).props('dense').classes('bg-blue-800 text-white font-bold text-xs')

                ui.separator().classes('my-2')
                client_table_container = ui.column().classes('w-full gap-2')

                def refresh_client_table():
                    client_table_container.clear()
                    clients_data = db.get_all_clients()

                    with client_table_container:
                        for store, contacts in clients_data.items():
                            with ui.card().classes('w-full p-3 border bg-gray-50 shadow-none gap-2'):
                                with ui.row().classes('w-full justify-between items-center border-b pb-1'):
                                    ui.label(store).classes('font-bold text-sm text-blue-900')
                                    ui.label(f'{len(contacts)} Total Contact(s)').classes('text-xs text-gray-500 font-semibold')

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
                                                
                                            with ui.badge(c, color='blue-2').classes('text-blue-900 text-xs px-2 py-1 items-center gap-1'):
                                                ui.button('×', on_click=remove_c).props('flat dense size=xs color=negative')
                                    else:
                                        ui.label('No contacts listed.').classes('text-xs text-gray-400 italic')

                                with ui.row().classes('w-full items-center gap-2 mt-1'):
                                    add_sec_input = ui.input(placeholder='+ Add Secondary Contact...').classes('w-8/12').props('dense outlined bg-white')
                                    
                                    def add_secondary(s=store, inp=add_sec_input):
                                        new_name = (inp.value or "").strip()
                                        if new_name:
                                            db.add_client_contact(s, new_name)
                                            refresh_client_table()
                                            ui.notify(f'Added contact "{new_name}"!', type='positive')

                                    ui.button('Add Contact', on_click=add_secondary).props('dense outline').classes('w-3/12 text-xs')

                refresh_client_table()