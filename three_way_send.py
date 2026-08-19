from nicegui import ui, app
import database as db
import pdf_generator as pdf_gen
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def create_three_way_send_page():
    current_tech = app.storage.user.get('tech_name', '')
    
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
    </style>
    ''', shared=True)

    with ui.card().classes('w-full max-w-4xl mx-auto p-6 my-6 bg-white shadow-xl rounded-lg text-sm'):
        
        # Header Row
        with ui.row().classes('w-full justify-between items-center border-b pb-3 mb-4'):
            with ui.column().classes('gap-0'):
                ui.label('UNIPOS RETAIL SOLUTIONS').classes('text-xl font-black text-blue-900')
                ui.label('Three-Way Dispatch & Email Center').classes('text-xs text-gray-500 font-bold')
            ui.button('👈 Back to Job Card', on_click=lambda: ui.navigate.to('/')).props('outline dense icon=arrow_back')

        # Selection Panel
        ui.label('Select Job Card & Target Store for 3-Way Dispatch').classes('font-bold text-sm text-blue-900 mb-2')
        
        clients_data = db.get_all_clients()
        store_names = list(clients_data.keys())
        
        with ui.grid(columns=2).classes('w-full gap-4 mb-4'):
            store_select = ui.select(store_names, label='Target Client Store').classes('w-full').props('outlined dense bg-white')
            
            # Fetch recent job cards for selection
            jc_history = db.get_job_card_history()
            jc_options = [f"{job['jc_no']} — {job.get('client', 'Client')} ({job['date_str']})" for job in jc_history]
            jc_select = ui.select(jc_options, label='Select Job Card Record').classes('w-full').props('outlined dense bg-white')

        # Dynamic Email Routing Preview Card
        email_preview_card = ui.card().classes('w-full p-4 bg-slate-50 border gap-2 mb-4')
        with email_preview_card:
            ui.label('📨 3-Way Dispatch Target Route Preview').classes('font-bold text-xs text-blue-900')
            primary_email_label = ui.label('Primary Store Email (To): [Select a store]').classes('text-xs text-gray-700 font-bold')
            secondary_emails_label = ui.label('Secondary Store Emails (CC): [None]').classes('text-xs text-gray-700')
            
            techs_db = db.get_technicians_db()
            tech_record = techs_db.get(current_tech, {})
            tech_email = tech_record.get('authorized_email', 'Not configured')
            tech_email_label = ui.label(f'Technician CC Email: {tech_email}').classes('text-xs text-gray-700')

            # Find Primary Dispatch Admin email
            primary_admin_email = "Not configured"
            for t_name, t_data in techs_db.items():
                if t_data.get('is_primary_dispatch'):
                    primary_admin_email = t_data.get('authorized_email', 'Not configured')
                    break
            admin_email_label = ui.label(f'Primary Admin CC Email: {primary_admin_email}').classes('text-xs text-gray-700 font-bold')

        # Safe extraction of store name string
        def on_store_change(e):
            val = e.value if hasattr(e, 'value') else (e.args if hasattr(e, 'args') else e)
            selected_store = str(val).strip() if isinstance(val, str) else str(val.get('value', '')) if isinstance(val, dict) else ""

            if selected_store and selected_store in clients_data:
                info = clients_data[selected_store]
                raw_emails = info.get('email', '')
                email_list = [em.strip() for em in raw_emails.replace(';', ',').split(',') if em.strip()]
                
                if email_list:
                    primary = email_list[0]
                    secondaries = ", ".join(email_list[1:]) if len(email_list) > 1 else "None"
                    primary_email_label.set_text(f'⭐ Primary Store Email (To): {primary}')
                    secondary_emails_label.set_text(f'📋 CC Store Emails: {secondaries}')
                else:
                    primary_email_label.set_text('⭐ Primary Store Email (To): [None configured]')
                    secondary_emails_label.set_text('📋 CC Store Emails: [None]')

        store_select.on('update:model-value', on_store_change)

        # SMTP Transmission Function using Unipos Corporate Settings
        def send_smtp_email(to_email, cc_list, subject, body_text, pdf_path):
            sender_email = "support4@unipos.co.za"
            sender_password = "6KYr56z6845J58"
            smtp_server = "smtp.unipos.co.za"
            smtp_port = 465

            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['Subject'] = subject
            msg['To'] = to_email

            all_recipients = [to_email]
            if cc_list:
                msg['Cc'] = ", ".join(cc_list)
                all_recipients.extend(cc_list)

            msg.attach(MIMEText(body_text, 'plain'))

            # Attach Job Card PDF
            if pdf_path and os.path.exists(pdf_path):
                try:
                    with open(pdf_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(pdf_path)}")
                        msg.attach(part)
                except Exception as e:
                    print(f"Attachment error: {e}")

            # Transmit via SMTP Port 465 (SSL/TLS)
            try:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, all_recipients, msg.as_string())
                server.quit()
                return True, "3-Way Dispatch sent successfully via Unipos Mail Server!"
            except Exception as e:
                return False, f"SMTP Error: {str(e)}"

        # Execution Handler
        def execute_three_way_dispatch():
            selected_jc_str = jc_select.value
            selected_store = store_select.value

            if not selected_jc_str or not selected_store:
                ui.notify('Please select both a target store and a job card record!', type='warning')
                return

            jc_no = selected_jc_str.split(' — ')[0].strip()
            target_job = next((j for j in jc_history if j['jc_no'] == jc_no), None)
            
            if not target_job:
                ui.notify('Could not locate job card record in database.', type='negative')
                return

            # Generate PDF file
            pdf_filename = f"{jc_no}.pdf"
            pdf_gen.generate_jobcard_pdf(target_job, pdf_filename)

            # Gather store emails
            store_info = clients_data.get(selected_store, {})
            raw_emails = store_info.get('email', '')
            email_list = [em.strip() for em in raw_emails.replace(';', ',').split(',') if em.strip()]

            primary_to = email_list[0] if email_list else 'support4@unipos.co.za'
            cc_list = email_list[1:] if len(email_list) > 1 else []

            # 1. Append technician email to CC loop if configured
            tech_email = tech_record.get('authorized_email', '').strip()
            if tech_email and tech_email not in cc_list:
                cc_list.append(tech_email)

            # 2. Append Primary Dispatch Admin email to CC loop if configured
            for t_name, t_data in techs_db.items():
                if t_data.get('is_primary_dispatch'):
                    admin_mail = t_data.get('authorized_email', '').strip()
                    if admin_mail and admin_mail not in cc_list and admin_mail != primary_to:
                        cc_list.append(admin_mail)
                    break

            subject = f"Unipos Job Card Dispatch - {jc_no} ({selected_store})"
            body = (
                f"Dear Client,\n\n"
                f"Please find attached official job card {jc_no} for {selected_store}.\n\n"
                f"System Details:\n"
                f"- Primary Tech: {target_job.get('tech', 'N/A')}\n"
                f"- Date: {target_job.get('date', 'N/A')}\n"
                f"- Total Due: R{target_job.get('total', 0.0):.2f}\n\n"
                f"Kind regards,\n"
                f"Unipos Retail Solutions Support Team"
            )

            # Fire off email
            success, message = send_smtp_email(primary_to, cc_list, subject, body, pdf_filename)
            
            if success:
                ui.notify(message, type='positive', timeout=5000)
            else:
                ui.notify(message, type='negative', timeout=8000)

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('🚀 Execute 3-Way Dispatch', on_click=execute_three_way_dispatch).props('color=primary dense').classes('text-xs font-bold')