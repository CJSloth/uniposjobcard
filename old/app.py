from nicegui import ui, app
import datetime
import database as db
import admin
import pdf_generator as pdf_gen
import os
from three_way_send import create_three_way_send_page

fault_suggestions = [
    "Till crash",
    "Slip Printer Offline",
    "Network Database Offline",
    "Scanner not reading barcode labels",
    "Server crash",
    "General maintenance"
]

quick_actions = {
    "Removed old PC": "Removed old PC terminal from service area.",
    "Changed IP": "Changed local IP address allocation rules.",
    "Setup Unipos": "Setup Unipos back-office retail environment.",
    "DB Backup": "Configured backup parameters and tested database sync.",
    "Tested / Complete": "Tested system end-to-end. Working perfectly."
}

callout_fee = 450.0
km_driven = 0.0
rate_per_km = 7.50
billable_hrs = 1.0
hourly_rate = 650.0

active_draft = {}
ui_glitter_enabled = True

@ui.page('/admin')
def admin_page():
    admin.create_admin_page()

@ui.page('/three-way-send')
def three_way_page():
    create_three_way_send_page()

@ui.page('/')
def main_jobcard_page():
    if 'tech_name' not in app.storage.user:
        app.storage.user['tech_name'] = ''
        app.storage.user['role'] = ''

    clients_db = db.get_all_clients()
    inventory_db = db.get_inventory_db()
    technicians_db = db.get_technicians_db()
    vehicles_list = ["None"] + db.get_vehicles()

    stock_rows = []

    today = datetime.date.today()
    if today.day == 1:
        if today.month == 1 and ui_glitter_enabled:
            ui.notify(f'🎉 Happy New Year {today.year}! Time to celebrate & crush new goals!', type='positive', position='top', timeout=6000)
        elif ui_glitter_enabled:
            months = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            ui.notify(f'☕ Hey, it is now {months[today.month]}! Congratulations on making it through last month!', type='info', position='top', timeout=5000)

    def calculate_stock_subtotal():
        total = 0.0
        for row in stock_rows:
            try:
                qty = float(row['qty'].value or 0)
                price = float(row['price'].value or 0)
                row_total = qty * price
                row['total'].set_text(f"R{row_total:.2f}")
                total += row_total
            except ValueError:
                pass
        return total

    def update_financials():
        labor_total = billable_hrs * hourly_rate
        travel_total = km_driven * rate_per_km
        stock_total = calculate_stock_subtotal()
        
        subtotal = float(callout_fee) + labor_total + travel_total + stock_total
        vat = subtotal * 0.15
        grand_total = subtotal + vat

        lbl_subtotal.set_text(f"R{subtotal:.2f}")
        lbl_vat.set_text(f"R{vat:.2f}")
        lbl_grand_total.set_text(f"R{grand_total:.2f}")
        return subtotal, vat, grand_total

    def on_client_select(e):
        selected_client = e.value
        if selected_client in clients_db:
            store_data = clients_db[selected_client]
            called_by_select.set_options(store_data["contacts"])
            called_by_select.value = store_data["contacts"][0] if store_data["contacts"] else ''
            client_email_input.value = store_data["email"]

    def on_called_by_change(e):
        val = (e.value or "").strip()
        selected_client = client_select.value
        if val and selected_client in clients_db:
            contacts_list = clients_db[selected_client]["contacts"]
            if val not in contacts_list:
                db.add_client_contact(selected_client, val)
                called_by_select.set_options(clients_db[selected_client]["contacts"])
                ui.notify(f'Saved "{val}" to {selected_client} in database!', type='positive')

    def on_fault_change(e):
        val = (e.value or "").strip()
        if val and val not in fault_suggestions:
            fault_suggestions.append(val)
            fault_select.set_options(fault_suggestions)
            ui.notify(f'Saved fault type: "{val}"', type='positive')

    def on_tech_change(e):
        selected_tech = e.value
        if selected_tech in technicians_db:
            tech_info = technicians_db[selected_tech]
            job_no = tech_info["current_jc"]
            input_jobcard_no.value = f"JC-{job_no}"
            
            assigned_v = tech_info.get("assigned_vehicle")
            vehicle_select.value = assigned_v if assigned_v else 'None'
            
            other_techs = [t for t in technicians_db.keys() if t != selected_tech]
            additional_techs_select.set_options(other_techs)

    def append_quick_action(e):
        if e.value in quick_actions:
            current_text = actions_taken.value or ""
            new_text = quick_actions[e.value]
            actions_taken.set_value(f"{current_text}\n• {new_text}".strip())

    def set_completion_status(completed: bool):
        if completed:
            incomplete_box.set_visibility(False)
            ui.notify('Marked Completed', type='positive')
        else:
            incomplete_box.set_visibility(True)
            ui.notify('Marked Incomplete - Reason & Tech Signature Required', type='warning')

    def save_jobcard_to_history(action_type="Saved"):
        global rate_per_km
        subtotal, vat, grand_total = update_financials()
        
        items_summary = []
        for r in stock_rows:
            if r['desc'].value:
                items_summary.append({
                    "item": r['desc'].value,
                    "qty": r['qty'].value,
                    "price": r['price'].value,
                    "serials": [inp.value for inp in r['sn_inputs'] if inp.value]
                })

        on_site_crew = ", ".join(additional_techs_select.value) if additional_techs_select.value else "None"
        full_actions_log = f"Primary Tech: {tech_select.value}\nAlso On Site: {on_site_crew}\n\n{actions_taken.value or ''}"

        veh_val = vehicle_select.value
        if veh_val == 'None':
            veh_val = ''

        current_store = client_select.value
        new_store_email = client_email_input.value.strip()
        if current_store in clients_db and new_store_email != clients_db[current_store]["email"]:
            db.update_store_email(current_store, new_store_email)
            ui.notify(f'Updated permanent dispatch email for store {current_store}!', type='info')

        record = {
            "jc_no": input_jobcard_no.value or "JC-0000",
            "tech": tech_select.value or "Unassigned",
            "client": current_store or "Unspecified Client",
            "called_by": called_by_select.value or "",
            "vehicle": veh_val,
            "date": date_in.value or datetime.date.today().strftime('%Y-%m-%d'),
            "fault": fault_select.value or "",
            "actions": full_actions_log,
            "items": items_summary,
            "km_driven": km_driven,
            "rate_per_km": rate_per_km,
            "billable_hrs": billable_hrs,
            "hourly_rate": hourly_rate,
            "callout_fee": callout_fee,
            "time_start": t_start.value or "",
            "time_end": t_end.value or "",
            "customer_comments": cust_comments.value or "",
            "payment_method": pay_method.value or "",
            "subtotal": subtotal,
            "vat": vat,
            "total": grand_total
        }
        
        db.save_job_card(record)
        
        if ui_glitter_enabled:
            ui.notify(f'🚀 📈 {record["jc_no"]} rocketed into database archive!', type='positive')
        else:
            ui.notify(f'{action_type}: {record["jc_no"]} saved permanently!', type='positive')
        
        refreshed_db = db.get_technicians_db()
        if record["tech"] in refreshed_db:
            input_jobcard_no.value = f"JC-{refreshed_db[record['tech']]['current_jc']}"

        rate_per_km = 7.50
        num_rate_km.value = 7.50
        return record

    def export_and_download_pdf():
        record = save_jobcard_to_history("PDF Exported")
        filename = f"{record['jc_no']}.pdf"
        pdf_gen.generate_jobcard_pdf(record, filename)
        ui.download(filename)
        ui.notify(f'Downloaded {filename} to your computer!', type='positive')

    def save_as_draft():
        global active_draft
        active_draft = {
            "jc_no": input_jobcard_no.value,
            "client": client_select.value,
            "called_by": called_by_select.value,
            "tech": tech_select.value,
            "vehicle": vehicle_select.value,
            "fault": fault_select.value,
            "actions": actions_taken.value,
            "saved_at": datetime.datetime.now().strftime('%H:%M:%S')
        }
        ui.notify(f'Draft saved at {active_draft["saved_at"]}', type='info')

    def open_draft_dialog():
        if not active_draft:
            ui.notify('No active draft found!', type='warning')
            return

        with ui.dialog() as draft_dlg, ui.card().classes('w-80 p-4 gap-2'):
            ui.label('📂 Load Saved Draft?').classes('font-bold text-blue-900 text-sm')
            ui.label(f'Draft: {active_draft.get("jc_no")} ({active_draft.get("client")})').classes('text-xs text-gray-600')
            ui.label(f'Saved at: {active_draft.get("saved_at")}').classes('text-xs text-gray-400')
            
            def load_draft():
                input_jobcard_no.value = active_draft.get("jc_no", "")
                client_select.value = active_draft.get("client", "")
                called_by_select.value = active_draft.get("called_by", "")
                tech_select.value = active_draft.get("tech", "")
                vehicle_select.value = active_draft.get("vehicle", "")
                fault_select.value = active_draft.get("fault", "")
                actions_taken.value = active_draft.get("actions", "")
                draft_dlg.close()
                ui.notify('Draft restored successfully!', type='positive')

            with ui.row().classes('w-full justify-end gap-2 mt-2'):
                ui.button('Cancel', on_click=draft_dlg.close).props('flat dense')
                ui.button('LOAD DRAFT', on_click=load_draft).props('color=primary dense')

        draft_dlg.open()

    def open_login_dialog():
        with ui.dialog().props('persistent') as login_dlg, ui.card().classes('w-96 p-6 bg-white items-center gap-4'):
            ui.label('🔐 Unipos Secure Sign-In').classes('font-bold text-lg text-blue-900 border-b pb-2 w-full text-center')
            ui.label('Enter your technician PIN to start.').classes('text-xs text-gray-500 text-center')
            
            pin_input = ui.input(label='Security PIN', password=True, placeholder='Enter PIN').classes('w-full').props('outlined dense autofocus')

            def perform_pin_login():
                val = (pin_input.value or "").strip()
                if not val:
                    ui.notify('Please enter your PIN!', type='negative')
                    return

                found_tech = None
                found_data = None
                for t_name, data in technicians_db.items():
                    if str(data.get('pin_code', '')) == val:
                        found_tech = t_name
                        found_data = data
                        break

                if found_tech and found_data:
                    role = 'Admin' if found_data.get('is_admin') else 'Technician'
                    app.storage.user['tech_name'] = found_tech
                    app.storage.user['role'] = role
                    tech_select.value = found_tech
                    login_dlg.close()
                    ui.notify(f'Successfully signed in as {found_tech}!', type='positive')
                    ui.navigate.to('/')
                else:
                    ui.notify('Invalid PIN! Access Denied.', type='negative')
                    pin_input.value = ''

            pin_input.on('keydown.enter', perform_pin_login)
            with ui.row().classes('w-full justify-center mt-2'):
                ui.button('🚀 Sign In', on_click=perform_pin_login).props('color=positive font-bold').classes('w-full text-xs')

        login_dlg.open()

    def logout_user():
        app.storage.user['tech_name'] = ''
        app.storage.user['role'] = ''
        ui.notify('Logged out successfully.', type='info')
        ui.navigate.to('/')

    if not app.storage.user.get('tech_name'):
        ui.timer(0.1, open_login_dialog, once=True)

    def open_fullscreen_signature_modal(canvas_id, title_text):
        with ui.dialog() as sig_dlg, ui.card().classes('w-full max-w-4xl p-6 bg-white items-center gap-4'):
            ui.label(f"✍️ {title_text} - Full Screen Signature Pad").classes('font-bold text-lg text-blue-900 border-b pb-2 w-full text-center')
            ui.label('Use your finger, stylus, or mouse to sign clearly below.').classes('text-xs text-gray-500')
            
            ui.html(f'<canvas id="{canvas_id}Modal" width="700" height="300" style="border:2px dashed #0056b3; background:#fff; cursor:crosshair; touch-action: none;"></canvas>')
            
            with ui.row().classes('w-full justify-between items-center mt-2'):
                def clear_modal():
                    ui.run_javascript(f'const c = document.getElementById("{canvas_id}Modal"); c.getContext("2d").clearRect(0, 0, c.width, c.height);')
                
                def capture_and_close():
                    ui.run_javascript(f'''
                        const src = document.getElementById("{canvas_id}Modal");
                        const dest = document.getElementById("{canvas_id}");
                        if (src && dest) {{
                            const dCtx = dest.getContext("2d");
                            dCtx.clearRect(0, 0, dest.width, dest.height);
                            dCtx.drawImage(src, 0, 0, dest.width, dest.height);
                        }}
                    ''')
                    sig_dlg.close()
                    ui.notify('Signature captured successfully!', type='positive')

                ui.button('Clear Pad', on_click=clear_modal).props('outline color=negative').classes('text-xs')
                with ui.row().classes('gap-2'):
                    ui.button('Cancel', on_click=sig_dlg.close).props('flat').classes('text-xs')
                    ui.button('✅ Accept & Save Signature', on_click=capture_and_close).props('color=positive font-bold').classes('text-xs')

        sig_dlg.open()
        ui.run_javascript(f'setTimeout(() => initCanvas("{canvas_id}Modal"), 200);')

    def create_stock_row_ui(item_name="", qty_val=1, price_val=0.0):
        with stock_container:
            with ui.row().classes('w-full items-start gap-1 mb-1 no-print-break') as row_container:
                desc = ui.select(
                    list(inventory_db.keys()), 
                    value=item_name if item_name in inventory_db else None, 
                    with_input=True
                ).classes('w-4/12').props('dense outlined')

                sn_container = ui.column().classes('w-2/12 gap-1')
                sn_inputs = []

                qty = ui.number(value=qty_val).classes('w-1/12').props('dense outlined min=1')
                price = ui.number(value=price_val).classes('w-2/12').props('outlined dense')
                
                total_lbl = ui.label('R0.00').classes('w-2/12 text-right font-bold text-xs text-blue-900 mt-2')

                row_dict = {
                    'container': row_container, 
                    'desc': desc, 
                    'sn_inputs': sn_inputs, 
                    'qty': qty, 
                    'price': price, 
                    'total': total_lbl
                }
                stock_rows.append(row_dict)

                def rebuild_sn_fields():
                    sn_container.clear()
                    sn_inputs.clear()
                    selected_item = desc.value
                    current_qty = int(qty.value or 1)
                    requires_sn = inventory_db.get(selected_item, {}).get('requires_sn', False)

                    with sn_container:
                        if requires_sn:
                            for i in range(current_qty):
                                label_text = f"S/N #{i+1}" if current_qty > 1 else "S/N Required"
                                inp = ui.input(placeholder=label_text).classes('w-full').props('dense outlined bg-color=red-1')
                                sn_inputs.append(inp)
                        else:
                            inp = ui.input(placeholder="N/A").classes('w-full').props('dense outlined disable bg-color=gray-1')
                            sn_inputs.append(inp)

                def on_item_change(e):
                    selected_item = e.value
                    if selected_item in inventory_db:
                        price.value = inventory_db[selected_item]['price']
                        rebuild_sn_fields()
                        update_financials()

                def on_qty_change(e):
                    rebuild_sn_fields()
                    update_financials()

                desc.on_value_change(on_item_change)
                qty.on_value_change(on_qty_change)
                price.on_value_change(lambda _: update_financials())

                if item_name:
                    on_item_change(type('Event', (), {'value': item_name}))
                else:
                    rebuild_sn_fields()

                def remove_row():
                    stock_rows.remove(row_dict)
                    stock_container.remove(row_container)
                    update_financials()

                ui.button('❌', on_click=remove_row).props('flat color=negative dense').classes('no-print mt-1')

    ui.colors(primary='#0056b3')

    with ui.left_drawer(value=False).classes('bg-gray-100 p-4 gap-3 no-print flex flex-col justify-between') as sidebar_drawer:
        with ui.column().classes('w-full gap-3'):
            ui.label('App Controls & Actions').classes('font-bold text-base border-b pb-2 text-blue-900 w-full')
            
            with ui.card().classes('w-full p-2 bg-white border border-blue-200 shadow-none gap-1'):
                if app.storage.user.get('tech_name'):
                    ui.label(f'👤 {app.storage.user.get("tech_name")}').classes('font-bold text-xs text-green-700 truncate')
                    ui.label(f'Role: {app.storage.user.get("role")}').classes('text-[10px] text-gray-500 truncate')
                    ui.button('🚪 Log Out / Switch PIN', on_click=logout_user).props('outline color=negative dense').classes('w-full text-xs mt-1')
                else:
                    ui.label('⚠️ Not Signed In').classes('font-bold text-xs text-orange-600')
                    ui.button('🔑 Sign In', on_click=open_login_dialog).props('color=primary dense').classes('w-full text-xs mt-1 font-bold')

            ui.separator().classes('my-1')
            
            ui.button('🚀 Save Job Card', on_click=lambda: save_jobcard_to_history("Final Saved")).props('color=positive icon=save').classes('w-full font-bold')
            ui.button('📝 Save as Draft', on_click=save_as_draft).props('outline icon=edit_note').classes('w-full')
            ui.button('🖨️ Print Document', on_click=lambda: (save_jobcard_to_history("Printed"), ui.run_javascript('window.print()'))).props('outline icon=print').classes('w-full')
            ui.button('💾 Save Backup PDF', on_click=export_and_download_pdf).props('outline icon=download').classes('w-full')
            ui.button('📧 3-Way Email Dispatch', on_click=lambda: (save_jobcard_to_history("Emailed"), ui.navigate.to('/three-way-send'))).props('color=primary icon=email').classes('w-full font-bold')
            
            ui.separator().classes('my-1')
            ui.label('Navigation & Recovery').classes('font-bold text-sm text-gray-700 w-full')
            ui.button('📂 Open Active Draft', on_click=open_draft_dialog).props('flat dense icon=folder_open').classes('w-full text-left')
            ui.button('🛠️ Management Portal (Admin)', on_click=lambda: ui.navigate.to('/admin')).props('flat dense icon=admin_panel_settings').classes('w-full text-left')

        with ui.card().classes('w-full p-2 bg-white border border-blue-200 shadow-none gap-1 mb-2'):
            ui.label('✨ UI Glitter & Animations').classes('font-bold text-[10px] text-blue-900')
            def toggle_glitter(e):
                global ui_glitter_enabled
                ui_glitter_enabled = e.value
                status = "Enabled 🎉" if e.value else "Disabled 🤫"
                ui.notify(f'UI Glitter & Effects: {status}', type='info')

            ui.switch('Enable Effects', value=ui_glitter_enabled, on_change=toggle_glitter).classes('text-xs')

    with ui.card().classes('jobcard-a4-sheet w-full max-w-2xl mx-auto p-3 bg-white shadow-lg rounded-none sm:rounded-lg my-1 text-xs'):
        
        with ui.row().classes('w-full justify-between items-start border-b pb-2 mb-2'):
            with ui.row().classes('items-start gap-2'):
                ui.button(on_click=lambda: sidebar_drawer.toggle()).props('flat dense icon=menu').classes('text-blue-900 no-print mt-1')
                
                with ui.column().classes('gap-0'):
                    ui.label('UNIPOS').classes('text-xl font-black text-blue-900 leading-none')
                    ui.label('RETAIL SOLUTIONS').classes('text-[10px] font-bold tracking-wider text-gray-700')
                    ui.label('Head Office | P.O. Box 28405, Danhof 9310').classes('text-[9px] text-gray-500')
                    ui.label('info@unipos.co.za | Tel: 086 110 2320').classes('text-[9px] text-gray-500')
            
            with ui.column().classes('items-end gap-0'):
                ui.label('Jobcard No:').classes('text-[10px] font-bold text-gray-600')
                default_jc_val = "JC-1042"
                logged_in_tech = app.storage.user.get('tech_name')
                if logged_in_tech in technicians_db:
                    default_jc_val = f"JC-{technicians_db[logged_in_tech]['current_jc']}"
                input_jobcard_no = ui.input(value=default_jc_val).classes('w-28 text-right font-black text-red-600').props('dense outlined input-class="text-red-600 font-black text-base text-right"')
                
                with ui.input(value=datetime.date.today().strftime('%Y-%m-%d')).props('dense outlined').classes('w-32 text-xs mt-1') as date_in:
                    with ui.menu():
                        ui.date().bind_value(date_in)

        with ui.card().classes('w-full p-2 bg-gray-50 border gap-2 mb-2 shadow-none'):
            with ui.grid(columns=2).classes('w-full gap-2'):
                # Row 1
                client_select = ui.select(
                    list(clients_db.keys()), 
                    label='To (Client):', 
                    with_input=True,
                    on_change=on_client_select
                ).classes('w-full').props('outlined dense')
                
                called_by_select = ui.select(
                    [], 
                    label='Called By:', 
                    with_input=True, 
                    new_value_mode='add',
                    on_change=on_called_by_change
                ).classes('w-full').props('outlined dense')

                # Row 2
                initial_client_key = list(clients_db.keys())[0] if clients_db else ''
                initial_email = clients_db.get(initial_client_key, {}).get('email', '') if initial_client_key else ''
                client_email_input = ui.input(label='Client Dispatch Email Address:', value=initial_email).classes('w-full').props('outlined dense bg-white')
                
                # Blank placeholder space next to Client Email
                ui.html('')

                # Row 3
                default_tech = app.storage.user.get('tech_name') if app.storage.user.get('tech_name') in technicians_db else list(technicians_db.keys())[0]
                tech_select = ui.select(
                    list(technicians_db.keys()), 
                    label='Technician 1 (Primary):', 
                    value=default_tech, 
                    on_change=on_tech_change
                ).classes('w-full').props('outlined dense')
                
                initial_other_techs = [t for t in technicians_db.keys() if t != default_tech]
                additional_techs_select = ui.select(
                    initial_other_techs,
                    multiple=True,
                    clearable=True,
                    label='Additional Technicians On Site:'
                ).classes('w-full').props('outlined dense use-chips options-dense')

                # Row 4
                assigned_veh = technicians_db.get(app.storage.user.get('tech_name'), {}).get('assigned_vehicle')
                default_veh_selection = assigned_veh if assigned_veh else 'None'
                vehicle_select = ui.select(
                    vehicles_list, 
                    label='Reg No (Vehicle):', 
                    value=default_veh_selection,
                    with_input=True,
                    new_value_mode='add'
                ).classes('w-full').props('outlined dense')
                
                ui.input(label='CRM No:', placeholder='CRM ID').classes('w-full').props('outlined dense')

                # Row 5
                ui.input(label='S/O No / Account No:', placeholder='Account Ref').classes('w-full').props('outlined dense')
                
                # Blank placeholder space next to Account No
                ui.html('')

        with ui.column().classes('w-full gap-1 mb-2'):
            fault_select = ui.select(
                fault_suggestions, 
                label='Details of Fault:', 
                with_input=True, 
                new_value_mode='add',
                on_change=on_fault_change
            ).classes('w-full').props('outlined dense')
            
            ui.select(
                list(quick_actions.keys()), 
                label='Action Taken by Technician:', 
                on_change=append_quick_action
            ).classes('w-full no-print').props('outlined dense')
            
            actions_taken = ui.textarea(
                label='Actions Log:',
                placeholder='Your work history timeline logs here...'
            ).classes('w-full').props('outlined rows=2')

        with ui.column().classes('w-full border-t pt-2 mb-2 gap-1'):
            ui.label('Stock / Spares / Line Items:').classes('font-bold text-xs text-gray-700')
            
            with ui.row().classes('w-full text-[10px] font-bold text-gray-600 bg-gray-100 p-1 rounded gap-1'):
                ui.label('Description / Item Name').classes('w-4/12')
                ui.label('Serial (S/N)').classes('w-2/12')
                ui.label('Qty').classes('w-1/12')
                ui.label('Price (Ex)').classes('w-2/12')
                ui.label('Line Total (Ex)').classes('w-2/12 text-right')

            stock_container = ui.column().classes('w-full gap-0')
            create_stock_row_ui()
            
            ui.button('➕ Add Stock Item', on_click=create_stock_row_ui).props('dense').classes('bg-green-600 text-white font-bold text-[10px] mt-1 no-print')

        with ui.grid(columns=2).classes('w-full gap-2 border-t pt-2'):
            
            with ui.column().classes('w-full gap-1'):
                with ui.row().classes('w-full gap-1'):
                    with ui.column().classes('w-1/2 gap-0'):
                        ui.label('Time Started:').classes('text-[10px] font-bold text-gray-600')
                        with ui.input(value='00:00').props('outlined dense').classes('w-full') as t_start:
                            with ui.menu().props('no-parent-event') as start_menu:
                                with ui.time().bind_value(t_start):
                                    with ui.row().classes('justify-end p-2 bg-white'):
                                        ui.button('DONE', on_click=start_menu.close).props('color=primary dense flat')
                            with t_start.add_slot('append'):
                                ui.icon('access_time').on('click', start_menu.open).classes('cursor-pointer')

                    with ui.column().classes('w-1/2 gap-0'):
                        ui.label('Time Completed:').classes('text-[10px] font-bold text-gray-600')
                        with ui.input(value='00:00').props('outlined dense').classes('w-full') as t_end:
                            with ui.menu().props('no-parent-event') as end_menu:
                                with ui.time().bind_value(t_end):
                                    with ui.row().classes('justify-end p-2 bg-white'):
                                        ui.button('DONE', on_click=end_menu.close).props('color=primary dense flat')
                            with t_end.add_slot('append'):
                                ui.icon('access_time').on('click', end_menu.open).classes('cursor-pointer')

                cust_comments = ui.textarea(label='Customer Comments:', placeholder='Feedback from client site...').classes('w-full').props('outlined rows=2')
                
                ui.label('Job Successfully Completed?').classes('font-bold text-xs mt-1')
                with ui.row().classes('gap-2'):
                    ui.button('YES', on_click=lambda: set_completion_status(True)).props('color=positive dense').classes('text-[10px]')
                    ui.button('NO', on_click=lambda: set_completion_status(False)).props('color=negative dense').classes('text-[10px]')

                with ui.card().classes('w-full p-2 bg-red-50 border border-red-200 gap-1 my-1 shadow-none') as incomplete_box:
                    ui.label('Reason Outstanding *').classes('font-bold text-[10px] text-red-700')
                    ui.input(placeholder='e.g. Waiting for replacement part...').classes('w-full').props('outlined dense bg-white')
                    
                    ui.label('Technician Signature * (Click to Expand)').classes('font-bold text-[10px] text-red-700 mt-1')
                    with ui.card().classes('w-full p-1 border border-dashed bg-white items-center justify-center shadow-none cursor-pointer').on('click', lambda: open_fullscreen_signature_modal('techCanvas', 'Technician Signature')):
                        ui.html('<canvas id="techCanvas" width="220" height="50" style="border:1px solid #ccc; background:#fff; pointer-events:none;"></canvas>')
                        ui.label('🔍 Click anywhere to sign full screen').classes('text-[9px] text-blue-700 font-bold no-print')

                incomplete_box.set_visibility(False)

                ui.label('Authorized Client Signature * (Click to Expand)').classes('font-bold text-[10px] text-gray-700 mt-1')
                with ui.card().classes('w-full p-1 border border-dashed bg-gray-50 items-center justify-center shadow-none cursor-pointer').on('click', lambda: open_fullscreen_signature_modal('clientCanvas', 'Client Signature')):
                    ui.html('<canvas id="clientCanvas" width="220" height="60" style="border:1px solid #ccc; background:#fff; pointer-events:none;"></canvas>')
                    ui.label('🔍 Click anywhere to sign full screen').classes('text-[9px] text-blue-700 font-bold no-print')

            with ui.card().classes('w-full bg-gray-50 p-2 border gap-1 shadow-none'):
                ui.label('Calculations Summary:').classes('font-bold text-xs text-gray-800 border-b pb-1 w-full')
                
                with ui.grid(columns=2).classes('w-full gap-1'):
                    def set_hrs(e):
                        global billable_hrs
                        billable_hrs = float(e.value or 0)
                        update_financials()
                    ui.number(label='Billable Hrs:', value=1.0, on_change=set_hrs).classes('w-full').props('outlined dense')

                    def set_rate(e):
                        global hourly_rate
                        hourly_rate = float(e.value or 0)
                        update_financials()
                    ui.number(label='Hourly Rate (R):', value=650.0, on_change=set_rate).classes('w-full').props('outlined dense')

                with ui.grid(columns=2).classes('w-full gap-1'):
                    def set_km(e):
                        global km_driven
                        km_driven = float(e.value or 0)
                        update_financials()
                    ui.number(label='KM Travelled:', value=0.0, on_change=set_km).classes('w-full').props('outlined dense')

                    def set_rate_km(e):
                        global rate_per_km
                        rate_per_km = float(e.value or 0)
                        update_financials()
                    num_rate_km = ui.number(label='Rate / KM (R):', value=7.50, on_change=set_rate_km).classes('w-full').props('outlined dense')

                def set_callout(e):
                    global callout_fee
                    callout_fee = float(e.value)
                    update_financials()

                ui.select({'450': 'R450 Base Call-Out', '650': 'R650 Fixed Call-Out'}, value='450', label='Call-Out Fee Option:', on_change=set_callout).classes('w-full').props('outlined dense')
                
                ui.separator()
                
                with ui.row().classes('w-full justify-between font-bold text-[11px]'):
                    ui.label('Sub Total (Ex):')
                    lbl_subtotal = ui.label('R0.00')

                with ui.row().classes('w-full justify-between text-[10px] text-gray-600'):
                    ui.label('15% VAT Value:')
                    lbl_vat = ui.label('R0.00')

                with ui.row().classes('w-full justify-between font-black text-xs bg-gray-900 text-white p-1 rounded'):
                    ui.label('Total Due (Inc):')
                    lbl_grand_total = ui.label('R0.00')

        with ui.card().classes('w-full p-2 bg-blue-50 border border-blue-200 mt-2 shadow-none'):
            ui.label('Method of Settlement / Payment Note:').classes('font-bold text-[10px] text-blue-900')
            pay_method = ui.select(
                ['Account', 'EFT', 'Cash',],
                value='On Account / Cash-Box Corporate Invoicing',
            ).classes('w-full').props('outlined dense bg-white')

        update_financials()

ui.add_head_html('''
<style>
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.fa-spinner { animation: spin 1.5s linear infinite; }

/* --- Sleek UI Polish & Smooth Corners (Inspired by modern G2/squircle design) --- */
.jobcard-a4-sheet {
    border-radius: 16px !important;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.08) !important;
    border: 1px solid #e2e8f0 !important;
}

/* Smooth out cards, buttons, and inputs globally */
.q-card {
    border-radius: 12px !important;
}

.q-btn {
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease-in-out !important;
}

.q-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 86, 179, 0.15);
}

.q-field__control {
    border-radius: 8px !important;
}

@media print {
    body { background: white !important; padding: 0 !important; margin: 0 !important; }
    .no-print { display: none !important; }
    .jobcard-a4-sheet {
        box-shadow: none !important;
        border: none !important;
        max-width: 100% !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        page-break-after: avoid;
        border-radius: 0 !important;
    }
    @page { size: A4 portrait; margin: 10mm; }
}
</style>

<script>
function initCanvas(id) {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let drawing = false;

    function getPos(e) {
        const rect = canvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        return { x: clientX - rect.left, y: clientY - rect.top };
    }

    function startDraw(e) { drawing = true; ctx.beginPath(); const p = getPos(e); ctx.moveTo(p.x, p.y); }
    function draw(e) { if (!drawing) return; e.preventDefault(); const p = getPos(e); ctx.lineTo(p.x, p.y); ctx.stroke(); }
    function stopDraw() { drawing = false; }

    canvas.addEventListener('mousedown', startDraw);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDraw);
    canvas.addEventListener('touchstart', startDraw, {passive: false});
    canvas.addEventListener('touchmove', draw, {passive: false});
    canvas.addEventListener('touchend', stopDraw);
}

document.addEventListener("DOMContentLoaded", function() {
    setTimeout(() => {
        initCanvas('clientCanvas');
        initCanvas('techCanvas');
    }, 1000);
});
</script>
''', shared=True)

if __name__ in {"__main__", "__mp_main__"}:
    port = int(os.environ.get("PORT", 8080))
    ui.run(title='Unipos Digital Job Card', port=port, host='0.0.0.0', reload=False, storage_secret='unipos_secure_secret_key_2026')