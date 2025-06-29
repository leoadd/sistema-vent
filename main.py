import flet as ft
import controllers
import models
import report_generator
from datetime import datetime, timedelta
import os # Import faltante añadido

# --- THEME SETTINGS ---
APP_PRIMARY_COLOR = ft.colors.PURPLE_ACCENT_700
APP_PRIMARY_COLOR_LIGHT = ft.colors.PURPLE_ACCENT_100
APP_TEXT_COLOR_PRIMARY = ft.colors.WHITE # ft.colors.WHITE es correcto
APP_TEXT_COLOR_SECONDARY = ft.colors.with_opacity(0.7, ft.colors.WHITE)
APP_TEXT_COLOR_PLACEHOLDER = ft.colors.with_opacity(0.5, ft.colors.WHITE)
APP_ERROR_COLOR = ft.colors.RED_ACCENT_200
FROSTED_GLASS_COLOR = ft.colors.with_opacity(0.65, ft.colors.LIGHT_BLUE_ACCENT_100)
FROSTED_GLASS_BORDER_COLOR = ft.colors.with_opacity(0.3, ft.colors.WHITE)
DIALOG_BG_COLOR = ft.colors.with_opacity(0.95, ft.colors.BLUE_GREY_900) # Ejemplo de color, verificar si ft.colors.BLUE_GREY_900 es el deseado

# --- Helper Global para Cerrar Diálogos ---
def close_dialog_global(page_instance: ft.Page, dialog_instance=None):
    # Si se pasa una instancia específica de diálogo, se cierra esa.
    # Si no, se intenta cerrar el diálogo actualmente asignado a la página.
    dlg_to_close = dialog_instance if dialog_instance else page_instance.dialog
    if dlg_to_close:
        dlg_to_close.open = False
        page_instance.update()

# --- Helper para crear campos de texto ---
def create_custom_textfield(label: str, ref: ft.Ref[ft.TextField] = None, password: bool = False, can_reveal_password: bool = False, width: int = 300, height: int = 48, keyboard_type: ft.KeyboardType = None, value=None, hint_text=None, on_submit=None, on_change=None, visible=True, multiline=False, min_lines=1, max_lines=1, dense=False, content_padding=10, text_size=15, label_size=14, border_radius=10, expand=False):
    return ft.TextField(
        ref=ref, label=label, width=width, password=password, keyboard_type=keyboard_type, value=value, hint_text=hint_text,
        label_style=ft.TextStyle(color=APP_TEXT_COLOR_PLACEHOLDER, weight=ft.FontWeight.NORMAL, size=label_size),
        height= height if not multiline else None,
        min_lines=min_lines if multiline else None,
        max_lines=max_lines if multiline else None,
        bgcolor=ft.colors.with_opacity(0.1, ft.colors.WHITE), border_color=ft.colors.with_opacity(0.2, ft.colors.WHITE),
        border_radius=border_radius, border_width=1, text_style=ft.TextStyle(color=APP_TEXT_COLOR_PRIMARY, size=text_size),
        cursor_color=APP_PRIMARY_COLOR, content_padding=content_padding, visible=visible, on_submit=on_submit, on_change=on_change,
        can_reveal_password=can_reveal_password, dense=dense, expand=expand
    )

# --- Vista de Login ---
def create_login_view(page: ft.Page, view_manager):
    title_text = ft.Text("Bienvenido", size=34, weight=ft.FontWeight.BOLD, color=APP_TEXT_COLOR_PRIMARY)
    subtitle_text = ft.Text("Inicia sesión para continuar", size=17, color=APP_TEXT_COLOR_SECONDARY, text_align=ft.TextAlign.CENTER)
    username_field = create_custom_textfield("Usuario", width=320, height=50, text_size=17, label_size=16)
    password_field = create_custom_textfield("Contraseña", width=320, height=50, text_size=17, label_size=16, password=True, can_reveal_password=True)
    error_message_text = ft.Text("", color=APP_ERROR_COLOR, size=14, visible=False, text_align=ft.TextAlign.CENTER, width=300)

    def handle_login_click(e):
        error_message_text.visible = False; page.update()
        username = username_field.value; password = password_field.value
        if not username or not password:
            error_message_text.value = "Por favor, ingresa usuario y contraseña."; error_message_text.visible = True; page.update(); return
        user_data = controllers.intentar_login(username, password)
        if user_data:
            page.session.set("user_id", user_data['id']); page.session.set("username", user_data['nombre_usuario']); page.session.set("user_role", user_data['rol'])
            view_manager.route_to("dashboard")
        else:
            error_message_text.value = "Usuario o contraseña incorrectos."; error_message_text.visible = True; page.update()

    login_button = ft.ElevatedButton(content=ft.Text("Iniciar Sesión", size=17, weight=ft.FontWeight.BOLD, color=APP_TEXT_COLOR_PRIMARY), on_click=handle_login_click, bgcolor=APP_PRIMARY_COLOR, width=320, height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12),elevation=2, shadow_color=ft.colors.with_opacity(0.3, ft.colors.BLACK)))
    forgot_password_button = ft.TextButton(content=ft.Text("¿Olvidaste tu contraseña?", size=15, color=APP_TEXT_COLOR_SECONDARY), on_click=lambda _: view_manager.route_to("recover_password_step1"))

    login_form_container = ft.Container(
        content=ft.Column([title_text, subtitle_text, ft.Container(height=20), username_field, ft.Container(height=10), password_field, ft.Container(height=5), error_message_text, ft.Container(height=20), login_button, ft.Container(height=10), forgot_password_button], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.SPACE_AROUND, spacing=0),
        width=370, padding=ft.padding.symmetric(vertical=30, horizontal=25), border_radius=20, bgcolor=FROSTED_GLASS_COLOR, border=ft.border.all(1, FROSTED_GLASS_BORDER_COLOR), shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color=ft.colors.with_opacity(0.1, ft.colors.BLACK), offset=ft.Offset(0, 5))
    )
    return [login_form_container]

# --- Vistas de Recuperación de Contraseña ---
def create_recover_pass_step1_view(page: ft.Page, view_manager):
    title_text = ft.Text("Recuperar Contraseña", size=28, weight=ft.FontWeight.BOLD, color=APP_TEXT_COLOR_PRIMARY)
    subtitle_text = ft.Text("Ingresa tu nombre de usuario para buscar tu cuenta.", size=16, color=APP_TEXT_COLOR_SECONDARY, text_align=ft.TextAlign.CENTER, width=300)
    username_field_recover = create_custom_textfield("Nombre de usuario", width=320)
    error_message_recover = ft.Text("", color=APP_ERROR_COLOR, size=14, visible=False, width=300, text_align=ft.TextAlign.CENTER)
    def handle_next_click(e):
        error_message_recover.visible = False; username = username_field_recover.value
        if not username: error_message_recover.value = "Por favor, ingresa un nombre de usuario."; error_message_recover.visible = True; error_message_recover.update(); return
        page.session.set("recovery_username", username)
        recovery_info = controllers.iniciar_recuperacion_contrasena(username)
        if recovery_info and recovery_info.get('pregunta_1') and recovery_info.get('pregunta_2'):
            page.session.set("recovery_q1", recovery_info['pregunta_1']); page.session.set("recovery_q2", recovery_info['pregunta_2'])
            view_manager.route_to("recover_password_step2")
        else: error_message_recover.value = "Usuario no encontrado o sin preguntas de seguridad."; error_message_recover.visible = True; error_message_recover.update()
    next_button = ft.ElevatedButton(content=ft.Text("Siguiente", size=17), on_click=handle_next_click, bgcolor=APP_PRIMARY_COLOR, width=300, height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)))
    back_button = ft.TextButton(content=ft.Text("Volver al Login", size=15, color=APP_TEXT_COLOR_SECONDARY), on_click=lambda _: view_manager.route_to("login"))
    form_container = ft.Container(content=ft.Column([title_text, subtitle_text, ft.Container(height=20), username_field_recover, error_message_recover, ft.Container(height=20), next_button, back_button], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10), width=350, padding=30, border_radius=20, bgcolor=FROSTED_GLASS_COLOR, border=ft.border.all(1,FROSTED_GLASS_BORDER_COLOR))
    return [form_container]

def create_recover_pass_step2_view(page: ft.Page, view_manager):
    username = page.session.get("recovery_username"); pregunta1_text = page.session.get("recovery_q1"); pregunta2_text = page.session.get("recovery_q2")
    if not all([username, pregunta1_text, pregunta2_text]): view_manager.route_to("login"); return [ft.Text("Error de sesión.", color=APP_ERROR_COLOR)]
    title_text = ft.Text(f"Hola, {username}", size=22, weight=ft.FontWeight.BOLD, color=APP_TEXT_COLOR_PRIMARY)
    subtitle_text = ft.Text("Responde tus preguntas de seguridad:", size=16, color=APP_TEXT_COLOR_SECONDARY)
    q1_display = ft.Text(pregunta1_text, color=APP_TEXT_COLOR_PRIMARY, weight=ft.FontWeight.SEMIBOLD); respuesta1_field = create_custom_textfield("Respuesta 1", width=320)
    q2_display = ft.Text(pregunta2_text, color=APP_TEXT_COLOR_PRIMARY, weight=ft.FontWeight.SEMIBOLD); respuesta2_field = create_custom_textfield("Respuesta 2", width=320)
    error_message_step2 = ft.Text("", color=APP_ERROR_COLOR, size=14, visible=False, width=300, text_align=ft.TextAlign.CENTER)
    def handle_verify_answers_click(e):
        error_message_step2.visible = False; r1 = respuesta1_field.value; r2 = respuesta2_field.value
        if not r1 or not r2: error_message_step2.value = "Debes responder ambas preguntas."; error_message_step2.visible = True; error_message_step2.update(); return
        if controllers.models.verificar_respuestas_seguridad(username, r1, r2):
            page.session.set("recovery_answer1_ok", r1); page.session.set("recovery_answer2_ok", r2); view_manager.route_to("recover_password_step3")
        else: error_message_step2.value = "Una o ambas respuestas son incorrectas."; error_message_step2.visible = True; error_message_step2.update()
    verify_button = ft.ElevatedButton(content=ft.Text("Verificar",size=17),on_click=handle_verify_answers_click,bgcolor=APP_PRIMARY_COLOR,width=300,height=50,style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)))
    back_button_s2 = ft.TextButton(content=ft.Text("Cancelar",size=15,color=APP_TEXT_COLOR_SECONDARY),on_click=lambda _: view_manager.route_to("login"))
    form_container = ft.Container(content=ft.Column([title_text,subtitle_text,ft.Container(height=15),q1_display,respuesta1_field,ft.Container(height=10),q2_display,respuesta2_field,error_message_step2,ft.Container(height=20),verify_button,back_button_s2],horizontal_alignment=ft.CrossAxisAlignment.START,spacing=8),width=350,padding=30,border_radius=20,bgcolor=FROSTED_GLASS_COLOR,border=ft.border.all(1,FROSTED_GLASS_BORDER_COLOR))
    return [form_container]

def create_recover_pass_step3_view(page: ft.Page, view_manager):
    username = page.session.get("recovery_username"); r1_ok = page.session.get("recovery_answer1_ok"); r2_ok = page.session.get("recovery_answer2_ok")
    if not all([username, r1_ok, r2_ok]): view_manager.route_to("login"); return [ft.Text("Error de sesión.", color=APP_ERROR_COLOR)]
    title_text = ft.Text("Crear Nueva Contraseña",size=24,weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_PRIMARY); subtitle_text = ft.Text(f"Establece una nueva contraseña para {username}.",size=16,color=APP_TEXT_COLOR_SECONDARY)
    new_password_field = create_custom_textfield("Nueva contraseña",password=True,can_reveal_password=True,width=320); confirm_password_field = create_custom_textfield("Confirmar contraseña",password=True,can_reveal_password=True,width=320)
    error_message_step3 = ft.Text("",color=APP_ERROR_COLOR,size=14,visible=False,width=300,text_align=ft.TextAlign.CENTER); success_message_step3 = ft.Text("",color=ft.colors.GREEN_ACCENT_400,size=14,visible=False,width=300,text_align=ft.TextAlign.CENTER)
    reset_button_ref = ft.Ref[ft.ElevatedButton]()
    def handle_reset_password_click(e):
        error_message_step3.visible=False; success_message_step3.visible=False; new_pass=new_password_field.value; confirm_pass=confirm_password_field.value
        if not new_pass or not confirm_pass: error_message_step3.value="Ambos campos son requeridos.";error_message_step3.visible=True;error_message_step3.update();return
        if new_pass!=confirm_pass: error_message_step3.value="Las contraseñas no coinciden.";error_message_step3.visible=True;error_message_step3.update();return
        if controllers.verificar_respuestas_y_establecer_nueva_contrasena(username,r1_ok,r2_ok,new_pass):
            success_message_step3.value="¡Contraseña restablecida!";success_message_step3.visible=True;new_password_field.disabled=True;confirm_password_field.disabled=True
            if reset_button_ref.current:reset_button_ref.current.disabled=True
            page.update(); page.session.remove("recovery_username");page.session.remove("recovery_q1");page.session.remove("recovery_q2");page.session.remove("recovery_answer1_ok");page.session.remove("recovery_answer2_ok")
            view_manager.route_to("login")
        else: error_message_step3.value="Error al restablecer.";error_message_step3.visible=True;error_message_step3.update()
    reset_button = ft.ElevatedButton(ref=reset_button_ref,content=ft.Text("Restablecer",size=17),on_click=handle_reset_password_click,bgcolor=APP_PRIMARY_COLOR,width=300,height=50,style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)))
    cancel_button_s3 = ft.TextButton(content=ft.Text("Cancelar",size=15,color=APP_TEXT_COLOR_SECONDARY),on_click=lambda _:view_manager.route_to("login"))
    form_container = ft.Container(content=ft.Column([title_text,subtitle_text,ft.Container(height=15),new_password_field,confirm_password_field,error_message_step3,success_message_step3,ft.Container(height=20),reset_button,cancel_button_s3],horizontal_alignment=ft.CrossAxisAlignment.CENTER,spacing=10),width=350,padding=30,border_radius=20,bgcolor=FROSTED_GLASS_COLOR,border=ft.border.all(1,FROSTED_GLASS_BORDER_COLOR))
    return [form_container]

# --- Vistas del Dashboard y Sub-vistas ---
def create_dashboard_view(page: ft.Page, view_manager):
    username = page.session.get("username") or "Usuario Desconocido"; user_role = page.session.get("user_role") or "N/A"
    dashboard_main_content = ft.Column([ ft.Text("Resumen General", size=28, weight=ft.FontWeight.BOLD, color=APP_TEXT_COLOR_PRIMARY), ft.Text(f"¡Bienvenido de nuevo, {username}!", size=20, color=APP_TEXT_COLOR_SECONDARY), ft.Container(height=20), ft.Container( content=ft.Text("Aquí se mostrará el contenido principal de la sección seleccionada.", color=APP_TEXT_COLOR_PRIMARY, italic=True), padding=30, bgcolor=ft.colors.with_opacity(0.08, ft.colors.WHITE), border_radius=15, expand=True, alignment=ft.alignment.center, ) ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.START,)
    main_content_area_ref = ft.Ref[ft.Container]()
    main_content_container = ft.Container(ref=main_content_area_ref, content=dashboard_main_content, expand=True, padding=ft.padding.symmetric(horizontal=30, vertical=25), alignment=ft.alignment.top_left,)
    nav_rail_destinations = [ft.NavigationRailDestination(icon=ft.icons.DASHBOARD_OUTLINED,selected_icon=ft.icons.DASHBOARD,label="Dashboard"), ft.NavigationRailDestination(icon=ft.icons.POINT_OF_SALE_OUTLINED,selected_icon=ft.icons.POINT_OF_SALE,label="Ventas"), ft.NavigationRailDestination(icon=ft.icons.INVENTORY_2_OUTLINED,selected_icon=ft.icons.INVENTORY_2,label="Inventario"), ft.NavigationRailDestination(icon=ft.icons.ASSESSMENT_OUTLINED,selected_icon=ft.icons.ASSESSMENT,label="Reportes"), ft.NavigationRailDestination(icon=ft.icons.GROUP_OUTLINED,selected_icon=ft.icons.GROUP,label="Usuarios"), ft.NavigationRailDestination(icon=ft.icons.SETTINGS_OUTLINED,selected_icon=ft.icons.SETTINGS,label="Configuración")]

    def change_main_content_area(selected_label: str):
        if main_content_area_ref.current:
            content_to_load = ft.Text(f"Contenido para: {selected_label} (No implementado)", color=APP_TEXT_COLOR_PRIMARY, size=20)
            user_id = page.session.get("user_id") # Obtener user_id aquí para usarlo en los checks de permisos
            if selected_label == "Dashboard": content_to_load = dashboard_main_content
            elif selected_label == "Usuarios":
                if user_role == "administrador": content_to_load = create_admin_users_view(page, view_manager)
                else: content_to_load = ft.Column([ft.Icon(ft.icons.LOCK_OUTLINE, size=48, color=APP_ERROR_COLOR), ft.Text("Acceso Denegado", size=24, color=APP_ERROR_COLOR)], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True)
            elif selected_label == "Inventario":
                if models.tiene_permiso(user_id,'ver_inventario')or models.tiene_permiso(user_id,'gestionar_inventario'): content_to_load = create_inventory_main_view(page, view_manager)
                else: content_to_load = ft.Column([ft.Icon(ft.icons.LOCK_OUTLINE,size=48,color=APP_ERROR_COLOR),ft.Text("Acceso Denegado",size=24,color=APP_ERROR_COLOR)],horizontal_alignment=ft.CrossAxisAlignment.CENTER,alignment=ft.MainAxisAlignment.CENTER,expand=True)
            elif selected_label == "Ventas":
                if models.tiene_permiso(user_id,'realizar_ventas'): content_to_load = create_pos_view(page, view_manager)
                else: content_to_load = ft.Column([ft.Icon(ft.icons.LOCK_OUTLINE,size=48,color=APP_ERROR_COLOR),ft.Text("Acceso Denegado",size=24,color=APP_ERROR_COLOR)],horizontal_alignment=ft.CrossAxisAlignment.CENTER,alignment=ft.MainAxisAlignment.CENTER,expand=True)
            elif selected_label == "Reportes":
                if models.tiene_permiso(user_id, 'generar_reportes_ventas'): content_to_load = create_reports_view(page, view_manager)
                else: content_to_load = ft.Column([ft.Icon(ft.icons.LOCK_OUTLINE,size=48,color=APP_ERROR_COLOR),ft.Text("Acceso Denegado",size=24,color=APP_ERROR_COLOR)],horizontal_alignment=ft.CrossAxisAlignment.CENTER,alignment=ft.MainAxisAlignment.CENTER,expand=True)
            elif selected_label == "Configuración": # Placeholder para Configuración
                if user_role == "administrador": content_to_load = create_settings_view(page, view_manager)
                else: content_to_load = ft.Column([ft.Icon(ft.icons.LOCK_OUTLINE,size=48,color=APP_ERROR_COLOR),ft.Text("Acceso Denegado",size=24,color=APP_ERROR_COLOR)],horizontal_alignment=ft.CrossAxisAlignment.CENTER,alignment=ft.MainAxisAlignment.CENTER,expand=True)


            main_content_area_ref.current.content = content_to_load; main_content_area_ref.current.update()

    navigation_rail = ft.NavigationRail(selected_index=0,label_type=ft.NavigationRailLabelType.ALL,min_width=100,min_extended_width=220,group_alignment=-0.95,destinations=nav_rail_destinations,on_change=lambda e:change_main_content_area(nav_rail_destinations[e.control.selected_index].label),bgcolor=ft.colors.with_opacity(0.05,ft.colors.BLACK),indicator_color=APP_PRIMARY_COLOR,indicator_shape=ft.StadiumBorder())

    def handle_logout(e): page.session.clear(); page.appbar=None; page.update(); view_manager.route_to("login")

    def open_change_password_dialog(e):
        current_user_id = page.session.get("user_id")
        if not current_user_id: page.show_snack_bar(ft.SnackBar(ft.Text("Error: No se pudo identificar al usuario."),open=True,bgcolor=APP_ERROR_COLOR)); return
        current_password_field_ref=ft.Ref[ft.TextField](); new_password_field_ref=ft.Ref[ft.TextField](); confirm_new_password_field_ref=ft.Ref[ft.TextField](); change_pass_error_text_ref=ft.Ref[ft.Text]()
        def do_change_password_action(e_dlg):
            current_pass=current_password_field_ref.current.value; new_pass=new_password_field_ref.current.value; confirm_pass=confirm_new_password_field_ref.current.value
            change_pass_error_text_ref.current.value=""; change_pass_error_text_ref.current.visible=False
            if not current_pass or not new_pass or not confirm_pass: change_pass_error_text_ref.current.value="Todos los campos son requeridos."; change_pass_error_text_ref.current.visible=True; change_pass_error_text_ref.current.update(); return
            if new_pass!=confirm_pass: change_pass_error_text_ref.current.value="La nueva contraseña y la confirmación no coinciden."; change_pass_error_text_ref.current.visible=True; change_pass_error_text_ref.current.update(); return
            resultado=controllers.cambiar_contrasena_propia(current_user_id,current_pass,new_pass)
            if"exitosa"in resultado: page.show_snack_bar(ft.SnackBar(ft.Text(resultado),open=True,bgcolor=ft.colors.GREEN_ACCENT_700)); close_dialog_global(page, page.dialog)
            else: change_pass_error_text_ref.current.value=resultado; change_pass_error_text_ref.current.visible=True; change_pass_error_text_ref.current.update()
        _current_pass_field=create_custom_textfield("Contraseña Actual",ref=current_password_field_ref,password=True,can_reveal_password=True,width=350); _new_pass_field=create_custom_textfield("Nueva Contraseña",ref=new_password_field_ref,password=True,can_reveal_password=True,width=350); _confirm_new_pass_field=create_custom_textfield("Confirmar Nueva Contraseña",ref=confirm_new_password_field_ref,password=True,can_reveal_password=True,width=350); _change_pass_error_text=ft.Text(ref=change_pass_error_text_ref,color=APP_ERROR_COLOR,visible=False,width=350,size=13,text_align=ft.TextAlign.CENTER)
        change_pass_dialog=ft.AlertDialog(modal=True,title=ft.Text("Cambiar Mi Contraseña",color=APP_TEXT_COLOR_PRIMARY,weight=ft.FontWeight.BOLD,size=20),content=ft.Container(content=ft.Column([_current_pass_field,_new_pass_field,_confirm_new_pass_field,_change_pass_error_text],spacing=10,tight=True,),width=380),actions=[ft.TextButton("Cancelar",on_click=lambda e:close_dialog_global(page,change_pass_dialog)),ft.ElevatedButton("Guardar Cambios",on_click=do_change_password_action,bgcolor=APP_PRIMARY_COLOR,color=APP_TEXT_COLOR_PRIMARY,style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))],actions_alignment=ft.MainAxisAlignment.END,shape=ft.RoundedRectangleBorder(radius=15),bgcolor=DIALOG_BG_COLOR)
        page.dialog=change_pass_dialog; change_pass_dialog.open=True; page.update()

    user_profile_menu = ft.PopupMenuButton(items=[ft.PopupMenuItem(text="Cambiar mi contraseña",on_click=open_change_password_dialog,icon=ft.icons.LOCK_PERSON_OUTLINED),ft.PopupMenuItem(height=1,bgcolor=ft.colors.with_opacity(0.2,ft.colors.WHITE)),ft.PopupMenuItem(text="Cerrar Sesión",on_click=handle_logout,icon=ft.icons.LOGOUT_ROUNDED)],content=ft.Row([ft.Icon(ft.icons.ACCOUNT_CIRCLE,color=APP_TEXT_COLOR_PRIMARY,size=30),ft.Container(width=5),ft.Text(username,color=APP_TEXT_COLOR_PRIMARY,weight=ft.FontWeight.SEMIBOLD,size=16,overflow=ft.TextOverflow.ELLIPSIS,width=120)],spacing=8,vertical_alignment=ft.CrossAxisAlignment.CENTER),tooltip="Ajustes de Usuario")
    dashboard_app_bar = ft.AppBar(leading_width=70,title=ft.Text("Panel Principal",color=APP_TEXT_COLOR_PRIMARY,weight=ft.FontWeight.BOLD,size=22),center_title=False,bgcolor=ft.colors.with_opacity(0.1,ft.colors.BLACK),elevation=0,toolbar_height=65,actions=[user_profile_menu,ft.Container(width=15)])
    page.appbar=dashboard_app_bar;page.vertical_alignment=ft.MainAxisAlignment.START;page.horizontal_alignment=ft.CrossAxisAlignment.START;page.padding=0
    return[ft.Row([navigation_rail,ft.VerticalDivider(width=1,thickness=1,color=ft.colors.with_opacity(0.1,ft.colors.WHITE)),main_content_container],expand=True,vertical_alignment=ft.CrossAxisAlignment.STRETCH,spacing=0)]

# --- Vista de Gestión de Usuarios (Admin) ---
def create_admin_users_view(page: ft.Page, view_manager):
    # ... (código de create_admin_users_view sin cambios significativos, usa close_dialog_global)
    admin_user_id = page.session.get("user_id"); users_datatable_ref = ft.Ref[ft.DataTable]()
    def load_users_into_table():
        if users_datatable_ref.current:
            users_list = controllers.listar_todos_los_usuarios_admin(admin_user_id); users_datatable_ref.current.rows.clear()
            if users_list:
                for user in users_list: users_datatable_ref.current.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(str(user['id']),color=APP_TEXT_COLOR_SECONDARY,size=13)), ft.DataCell(ft.Text(user['nombre_usuario'],color=APP_TEXT_COLOR_PRIMARY,size=14)), ft.DataCell(ft.Text(user['rol'].capitalize()if user['rol']else"N/A",color=APP_TEXT_COLOR_PRIMARY,size=14)), ft.DataCell(ft.Row([ft.IconButton(ft.icons.EDIT_OUTLINED,icon_color=ft.colors.AMBER_ACCENT_200,icon_size=18,tooltip="Editar Usuario",on_click=lambda e,u=user:open_user_dialog(u)), ft.IconButton(ft.icons.ADMIN_PANEL_SETTINGS_OUTLINED,icon_color=ft.colors.CYAN_A200,icon_size=18,tooltip="Gestionar Permisos",on_click=lambda e,u=user:open_permissions_dialog(u)), ft.IconButton(ft.icons.DELETE_OUTLINE,icon_color=APP_ERROR_COLOR,icon_size=18,tooltip="Eliminar Usuario",on_click=lambda e,u_id=user['id'],u_name=user['nombre_usuario']:confirm_delete_user(u_id,u_name))],spacing=0,alignment=ft.MainAxisAlignment.START))]))
            users_datatable_ref.current.update()
    dialog_title_text_ref=ft.Ref[ft.Text](); dialog_username_field_ref=ft.Ref[ft.TextField](); dialog_password_field_ref=ft.Ref[ft.TextField](); dialog_role_dropdown_ref=ft.Ref[ft.Dropdown](); dialog_q1_field_ref=ft.Ref[ft.TextField](); dialog_a1_field_ref=ft.Ref[ft.TextField](); dialog_q2_field_ref=ft.Ref[ft.TextField](); dialog_a2_field_ref=ft.Ref[ft.TextField](); dialog_error_text_ref=ft.Ref[ft.Text](); current_edit_user_id_holder={"id":None}

    def save_user_data(e): # Usa close_dialog_global(page, user_form_dialog_obj)
        username=dialog_username_field_ref.current.value; password=dialog_password_field_ref.current.value; role=dialog_role_dropdown_ref.current.value; q1=dialog_q1_field_ref.current.value or None; a1=dialog_a1_field_ref.current.value or None; q2=dialog_q2_field_ref.current.value or None; a2=dialog_a2_field_ref.current.value or None
        dialog_error_text_ref.current.visible=False;dialog_error_text_ref.current.update()
        if not username or not role:dialog_error_text_ref.current.value="Nombre de usuario y rol son requeridos.";dialog_error_text_ref.current.visible=True;dialog_error_text_ref.current.update();return
        if current_edit_user_id_holder["id"]is None:
            if not password:dialog_error_text_ref.current.value="La contraseña es requerida para nuevos usuarios.";dialog_error_text_ref.current.visible=True;dialog_error_text_ref.current.update();return
            new_id=controllers.crear_nuevo_usuario_admin(admin_user_id,username,password,role,q1,a1,q2,a2)
            if new_id:load_users_into_table();close_dialog_global(page, user_form_dialog_obj);page.show_snack_bar(ft.SnackBar(ft.Text(f"Usuario '{username}' creado exitosamente."),open=True,bgcolor=ft.colors.GREEN_ACCENT_700))
            else:dialog_error_text_ref.current.value="Error al crear usuario (posiblemente el nombre de usuario ya existe).";dialog_error_text_ref.current.visible=True;dialog_error_text_ref.current.update()
        else:
            success=controllers.modificar_usuario_admin(admin_id=admin_user_id,usuario_id_a_modificar=current_edit_user_id_holder["id"],nombre_usuario=username,rol=role,pregunta1=q1,respuesta1=a1,pregunta2=q2,respuesta2=a2,nueva_contrasena=password if password else None)
            if success:load_users_into_table();close_dialog_global(page, user_form_dialog_obj);page.show_snack_bar(ft.SnackBar(ft.Text(f"Usuario '{username}' actualizado."),open=True,bgcolor=ft.colors.GREEN_ACCENT_700))
            else:dialog_error_text_ref.current.value="Error al modificar usuario.";dialog_error_text_ref.current.visible=True;dialog_error_text_ref.current.update()
    _dialog_username_field=create_custom_textfield("Nombre de Usuario",ref=dialog_username_field_ref,width=360); _dialog_password_field=create_custom_textfield("Contraseña",ref=dialog_password_field_ref,password=True,can_reveal_password=True,width=360); _dialog_role_dropdown=ft.Dropdown(ref=dialog_role_dropdown_ref,label="Rol",text_style=ft.TextStyle(color=APP_TEXT_COLOR_PRIMARY,size=15),label_style=ft.TextStyle(color=APP_TEXT_COLOR_PLACEHOLDER,size=15),bgcolor=ft.colors.with_opacity(0.15,ft.colors.WHITE),border_color=ft.colors.with_opacity(0.3,ft.colors.WHITE),border_radius=12,width=360,height=50,content_padding=12,options=[ft.dropdown.Option("administrador","Administrador"),ft.dropdown.Option("empleado","Empleado")]); _dialog_q1_field=create_custom_textfield("Pregunta de Seguridad 1 (opcional)",ref=dialog_q1_field_ref,width=360); _dialog_a1_field=create_custom_textfield("Respuesta a Pregunta 1 (opcional)",ref=dialog_a1_field_ref,width=360); _dialog_q2_field=create_custom_textfield("Pregunta de Seguridad 2 (opcional)",ref=dialog_q2_field_ref,width=360); _dialog_a2_field=create_custom_textfield("Respuesta a Pregunta 2 (opcional)",ref=dialog_a2_field_ref,width=360); _dialog_error_text=ft.Text(ref=dialog_error_text_ref,color=APP_ERROR_COLOR,visible=False,width=360,text_align=ft.TextAlign.CENTER,size=13)
    user_form_dialog_obj=ft.AlertDialog(modal=True,title=ft.Text(ref=dialog_title_text_ref,size=22,weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_PRIMARY),content=ft.Container(content=ft.Column([_dialog_username_field,_dialog_password_field,_dialog_role_dropdown,ft.Divider(height=10,color=ft.colors.TRANSPARENT),ft.Text("Preguntas de Seguridad (Opcional)",color=APP_TEXT_COLOR_SECONDARY,style=ft.TextThemeStyle.BODY_SMALL),_dialog_q1_field,_dialog_a1_field,_dialog_q2_field,_dialog_a2_field,_dialog_error_text],spacing=10,tight=False,scroll=ft.ScrollMode.ADAPTIVE),width=400,height=480),actions=[ft.TextButton("Cancelar",on_click=lambda e: close_dialog_global(page, user_form_dialog_obj)),ft.ElevatedButton("Guardar",on_click=save_user_data,bgcolor=APP_PRIMARY_COLOR,color=APP_TEXT_COLOR_PRIMARY,style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))],actions_alignment=ft.MainAxisAlignment.END,shape=ft.RoundedRectangleBorder(radius=15),bgcolor=DIALOG_BG_COLOR)
    def open_user_dialog(user_data_to_edit=None): # Usa close_dialog_global
        page.dialog=user_form_dialog_obj;dialog_error_text_ref.current.visible=False;_dialog_username_field.error_text=None
        if user_data_to_edit:
            current_edit_user_id_holder["id"]=user_data_to_edit['id'];dialog_title_text_ref.current.value=f"Editar Usuario";full_user_details=controllers.obtener_detalles_usuario_admin(admin_user_id,current_edit_user_id_holder["id"])
            _dialog_username_field.value=full_user_details['nombre_usuario'];_dialog_password_field.label="Nueva Contraseña";_dialog_password_field.hint_text="Dejar vacío para no cambiar";_dialog_password_field.value="";_dialog_role_dropdown.value=full_user_details['rol'];_dialog_q1_field.value=full_user_details.get('pregunta_seguridad_1',"");_dialog_a1_field.value=full_user_details.get('respuesta_seguridad_1',"");_dialog_q2_field.value=full_user_details.get('pregunta_seguridad_2',"");_dialog_a2_field.value=full_user_details.get('respuesta_seguridad_2',"")
        else:
            current_edit_user_id_holder["id"]=None;dialog_title_text_ref.current.value="Agregar Nuevo Usuario";_dialog_username_field.value="";_dialog_password_field.label="Contraseña";_dialog_password_field.hint_text="";_dialog_password_field.value="";_dialog_role_dropdown.value="empleado";_dialog_q1_field.value="";_dialog_a1_field.value="";_dialog_q2_field.value="";_dialog_a2_field.value=""
        page.dialog.open=True;page.update()
    def confirm_delete_user(user_id_to_delete,username_to_delete): # Usa close_dialog_global
        def do_delete(e):
            close_dialog_global(page, page.dialog);success=controllers.eliminar_usuario_admin(admin_user_id,user_id_to_delete)
            if success:load_users_into_table();page.show_snack_bar(ft.SnackBar(ft.Text(f"Usuario '{username_to_delete}' eliminado."),open=True,bgcolor=ft.colors.GREEN_ACCENT_700))
            else:page.show_snack_bar(ft.SnackBar(ft.Text(f"Error: No se pudo eliminar a '{username_to_delete}'. Verifica que no sea el único administrador."),open=True,bgcolor=APP_ERROR_COLOR,duration=5000))
        confirm_dialog=ft.AlertDialog(modal=True,title=ft.Text("Confirmar Eliminación",color=APP_TEXT_COLOR_PRIMARY),content=ft.Text(f"¿Estás seguro de que quieres eliminar al usuario '{username_to_delete}'? Esta acción no se puede deshacer.",color=APP_TEXT_COLOR_SECONDARY),actions=[ft.TextButton("Cancelar",on_click=lambda e:close_dialog_global(page,confirm_dialog)),ft.ElevatedButton("Eliminar",on_click=do_delete,bgcolor=APP_ERROR_COLOR,color=APP_TEXT_COLOR_PRIMARY,style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))],shape=ft.RoundedRectangleBorder(radius=15),bgcolor=DIALOG_BG_COLOR)
        page.dialog=confirm_dialog;confirm_dialog.open=True;page.update()
    permissions_checkboxes_col_ref=ft.Ref[ft.Column]();current_permissions_user_id_holder={"id":None};permissions_dialog_title_ref=ft.Ref[ft.Text]()
    def save_permissions(e): # Usa close_dialog_global
        if permissions_checkboxes_col_ref.current and current_permissions_user_id_holder["id"]is not None:
            for ctrl_row in permissions_checkboxes_col_ref.current.controls:
                if isinstance(ctrl_row,ft.Row)and len(ctrl_row.controls)>0 and isinstance(ctrl_row.controls[0],ft.Checkbox):
                    chk=ctrl_row.controls[0];perm_name=chk.data;has_perm=chk.value
                    controllers.gestionar_permiso_usuario_admin(admin_user_id,current_permissions_user_id_holder["id"],perm_name,otorgar=has_perm)
            page.show_snack_bar(ft.SnackBar(ft.Text("Permisos actualizados."),open=True,bgcolor=ft.colors.GREEN_ACCENT_700));close_dialog_global(page, permissions_form_dialog_obj)
        else:page.show_snack_bar(ft.SnackBar(ft.Text("Error al guardar permisos (referencias no encontradas)."),open=True,bgcolor=APP_ERROR_COLOR))
    permissions_form_dialog_obj=ft.AlertDialog(modal=True,title=ft.Text(ref=permissions_dialog_title_ref,size=20,weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_PRIMARY),content=ft.Container(content=ft.Column(ref=permissions_checkboxes_col_ref,spacing=1,scroll=ft.ScrollMode.ADAPTIVE),width=400,height=350,padding=ft.padding.only(top=5,right=5)),actions=[ft.TextButton("Cancelar",on_click=lambda e:close_dialog_global(page, permissions_form_dialog_obj)),ft.ElevatedButton("Guardar Permisos",on_click=save_permissions,bgcolor=APP_PRIMARY_COLOR,color=APP_TEXT_COLOR_PRIMARY,style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))],actions_alignment=ft.MainAxisAlignment.END,shape=ft.RoundedRectangleBorder(radius=15),bgcolor=DIALOG_BG_COLOR)
    def open_permissions_dialog(user_data_for_perms): # Usa close_dialog_global
        current_permissions_user_id_holder["id"]=user_data_for_perms['id'];permissions_dialog_title_ref.current.value=f"Permisos para: {user_data_for_perms['nombre_usuario']}"
        perm_info=controllers.obtener_permisos_de_usuario_admin(admin_user_id,current_permissions_user_id_holder["id"]);checkbox_controls=[]
        if perm_info:
            all_system_perms=perm_info['todos_los_permisos'];user_has_perms=perm_info['permisos_usuario']
            for perm_name in sorted(all_system_perms):
                chk=ft.Checkbox(data=perm_name,value=(perm_name in user_has_perms),fill_color=APP_PRIMARY_COLOR)
                checkbox_controls.append(ft.Row([chk,ft.Text(perm_name.replace("_"," ").capitalize(),color=APP_TEXT_COLOR_PRIMARY,expand=True,size=13)],spacing=8,vertical_alignment=ft.CrossAxisAlignment.CENTER))
            permissions_checkboxes_col_ref.current.controls=checkbox_controls
        else:permissions_checkboxes_col_ref.current.controls=[ft.Text("No se pudieron cargar los permisos.",color=APP_ERROR_COLOR)]
        page.dialog=permissions_form_dialog_obj;permissions_form_dialog_obj.open=True;page.update()
    datatable=ft.DataTable(ref=users_datatable_ref,heading_row_color=ft.colors.with_opacity(0.05,ft.colors.WHITE),heading_row_height=40,data_row_min_height=45,data_row_max_height=50,column_spacing=15,divider_thickness=0.5,columns=[ft.DataColumn(ft.Text("ID",weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_SECONDARY,size=12)),ft.DataColumn(ft.Text("Usuario",weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_PRIMARY,size=14)),ft.DataColumn(ft.Text("Rol",weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_PRIMARY,size=14)),ft.DataColumn(ft.Container(content=ft.Text("Acciones",weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_SECONDARY,size=14),alignment=ft.alignment.center_left,padding=ft.padding.only(left=0)))],rows=[],expand=True)
    load_users_into_table()
    return ft.Column([ft.Row([ft.Text("Gestión de Usuarios",size=26,weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_PRIMARY),ft.ElevatedButton("Agregar Usuario",icon=ft.icons.ADD_CIRCLE_OUTLINE,on_click=lambda e:open_user_dialog(None),bgcolor=APP_PRIMARY_COLOR,color=APP_TEXT_COLOR_PRIMARY,height=40,style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))],alignment=ft.MainAxisAlignment.SPACE_BETWEEN,vertical_alignment=ft.CrossAxisAlignment.CENTER),ft.Divider(height=1,thickness=0.5,color=FROSTED_GLASS_BORDER_COLOR),ft.Container(height=10),ft.Container(content=datatable,expand=True)],expand=True,spacing=15)

# --- Vista Principal de Gestión de Inventario ---
def create_inventory_main_view(page: ft.Page, view_manager):
    # ... (código de create_inventory_main_view sin cambios significativos, usa close_dialog_global) ...
    inventory_tab_content_area = ft.Ref[ft.Container](); current_user_id = page.session.get("user_id")
    can_manage_inventory=models.tiene_permiso(current_user_id,'gestionar_inventario'); can_manage_categories=models.tiene_permiso(current_user_id,'gestionar_categorias')or can_manage_inventory; can_manage_providers=models.tiene_permiso(current_user_id,'gestionar_proveedores')or can_manage_inventory; can_adjust_stock=models.tiene_permiso(current_user_id,'ajustar_stock')or can_manage_inventory; can_see_purchase_price=models.tiene_permiso(current_user_id,'ver_precio_compra')or can_manage_inventory
    def get_products_view():
        products_datatable_ref=ft.Ref[ft.DataTable]();prod_search_field_ref=ft.Ref[ft.TextField]();_prod_dialog_title_ref=ft.Ref[ft.Text]();_prod_name_ref=ft.Ref[ft.TextField]();_prod_code_ref=ft.Ref[ft.TextField]();_prod_desc_ref=ft.Ref[ft.TextField]();_prod_cat_dd_ref=ft.Ref[ft.Dropdown]();_prod_prov_dd_ref=ft.Ref[ft.Dropdown]();_prod_pcompra_ref=ft.Ref[ft.TextField]();_prod_pmenudeo_ref=ft.Ref[ft.TextField]();_prod_pmayoreo_ref=ft.Ref[ft.TextField]();_prod_cantmayoreo_ref=ft.Ref[ft.TextField]();_prod_stock_ref=ft.Ref[ft.TextField]();_prod_stockmin_ref=ft.Ref[ft.TextField]();_prod_unidad_ref=ft.Ref[ft.TextField]();_prod_error_ref=ft.Ref[ft.Text]();_current_edit_prod_id_holder={"id":None};cat_options_prod_dialog=[];prov_options_prod_dialog=[]
        def load_products_table(search_term=None):
            if products_datatable_ref.current:
                prods=controllers.obtener_productos_para_vista(current_user_id,limit=200,nombre_filtro=search_term);products_datatable_ref.current.rows.clear()
                if isinstance(prods,list):
                    for p in prods:
                        stock_val=p.get('stock_actual',0);stock_min_val=p.get('stock_minimo',0);stock_color=APP_TEXT_COLOR_PRIMARY
                        if stock_val==0:stock_color=APP_ERROR_COLOR
                        elif stock_val<=stock_min_val and stock_min_val > 0:stock_color=ft.colors.AMBER_ACCENT_400
                        products_datatable_ref.current.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(p.get('codigo_barras','N/A'),size=12,color=APP_TEXT_COLOR_SECONDARY)),ft.DataCell(ft.Text(p['nombre_producto'],size=13,weight=ft.FontWeight.W_500,color=APP_TEXT_COLOR_PRIMARY)),ft.DataCell(ft.Text(p.get('nombre_categoria','N/A'),size=12,color=APP_TEXT_COLOR_SECONDARY)),ft.DataCell(ft.Text(f"{p.get('precio_venta_menudeo',0):.2f}",size=13,text_align=ft.TextAlign.RIGHT,color=APP_TEXT_COLOR_PRIMARY)),ft.DataCell(ft.Text(f"{stock_val} {p.get('unidad_medida','U')}",size=13,text_align=ft.TextAlign.RIGHT,color=stock_color)),ft.DataCell(ft.Row([ft.IconButton(ft.icons.EDIT_OUTLINED,icon_color=ft.colors.AMBER_ACCENT_200,icon_size=18,tooltip="Editar",on_click=lambda e,prod=p:open_product_dialog(prod)if can_manage_inventory else None,disabled=not can_manage_inventory),ft.IconButton(ft.icons.ADD_SHOPPING_CART_ROUNDED,icon_color=ft.colors.GREEN_ACCENT_200,icon_size=18,tooltip="Registrar Entrada Stock",on_click=lambda e,prod_id=p['id'],prod_name=p['nombre_producto']:open_stock_entry_dialog(prod_id,prod_name)if can_adjust_stock else None,disabled=not can_adjust_stock),ft.IconButton(ft.icons.DELETE_SWEEP_OUTLINED,icon_color=APP_ERROR_COLOR,icon_size=18,tooltip="Marcar Inactivo",on_click=lambda e,prod_id=p['id'],prod_name=p['nombre_producto']:confirm_delete_product(prod_id,prod_name)if can_manage_inventory else None,disabled=not can_manage_inventory)],spacing=0,alignment=ft.MainAxisAlignment.START)if can_manage_inventory or can_adjust_stock else ft.Container(width=0))],data=p['id']))
                products_datatable_ref.current.update()
        def save_product_data(e):
            _prod_error_ref.current.visible=False;_prod_error_ref.current.update()
            if not _prod_name_ref.current.value or not _prod_pmenudeo_ref.current.value:_prod_error_ref.current.value="Nombre y Precio Menudeo son requeridos.";_prod_error_ref.current.visible=True;_prod_error_ref.current.update();return
            try:precio_menudeo=float(_prod_pmenudeo_ref.current.value);precio_compra_val=_prod_pcompra_ref.current.value;precio_compra=float(precio_compra_val)if can_see_purchase_price and precio_compra_val else 0.0;stock=int(_prod_stock_ref.current.value or 0);stock_min=int(_prod_stockmin_ref.current.value or 0);cant_mayoreo=int(_prod_cantmayoreo_ref.current.value)if _prod_cantmayoreo_ref.current.value else None;precio_mayoreo_val=_prod_pmayoreo_ref.current.value;precio_mayoreo=float(precio_mayoreo_val)if precio_mayoreo_val else None
            except ValueError:_prod_error_ref.current.value="Precios, Stock y Cantidades deben ser números válidos.";_prod_error_ref.current.visible=True;_prod_error_ref.current.update();return
            data={"nombre_producto":_prod_name_ref.current.value,"codigo_barras":_prod_code_ref.current.value or None,"descripcion":_prod_desc_ref.current.value or None,"categoria_id":int(_prod_cat_dd_ref.current.value)if _prod_cat_dd_ref.current.value else None,"proveedor_id":int(_prod_prov_dd_ref.current.value)if _prod_prov_dd_ref.current.value else None,"precio_venta_menudeo":precio_menudeo,"precio_venta_mayoreo":precio_mayoreo,"cantidad_para_mayoreo":cant_mayoreo,"stock_actual":stock,"stock_minimo":stock_min,"unidad_medida":_prod_unidad_ref.current.value or"unidad"}
            if can_see_purchase_price:data["precio_compra"]=precio_compra
            result=controllers.crear_nuevo_producto_admin(current_user_id,**data)if _current_edit_prod_id_holder["id"]is None else controllers.actualizar_producto_admin(current_user_id,_current_edit_prod_id_holder["id"],**data)
            if result and(result.get("id")or result.get("success")):load_products_table(prod_search_field_ref.current.value if prod_search_field_ref.current else None);close_dialog_global(page, page.dialog);page.show_snack_bar(ft.SnackBar(ft.Text(f"Producto '{data['nombre_producto']}' guardado."),open=True,bgcolor=ft.colors.GREEN_ACCENT_700))
            else:_prod_error_ref.current.value=result.get("error","Error desconocido.");_prod_error_ref.current.visible=True;_prod_error_ref.current.update()
        product_dialog_layout=ft.Column([create_custom_textfield("Nombre Producto*",ref=_prod_name_ref,width=360),create_custom_textfield("Código Barras",ref=_prod_code_ref,width=360),create_custom_textfield("Descripción",ref=_prod_desc_ref,width=360,multiline=True,min_lines=2,max_lines=3),ft.Row([ft.Dropdown(ref=_prod_cat_dd_ref,label="Categoría",options=[],width=175,height=48,text_style=ft.TextStyle(color=APP_TEXT_COLOR_PRIMARY,size=14),bgcolor=ft.colors.with_opacity(0.1,ft.colors.WHITE),border_radius=10,content_padding=10,label_style=ft.TextStyle(color=APP_TEXT_COLOR_PLACEHOLDER,size=14)),ft.Dropdown(ref=_prod_prov_dd_ref,label="Proveedor",options=[],width=175,height=48,text_style=ft.TextStyle(color=APP_TEXT_COLOR_PRIMARY,size=14),bgcolor=ft.colors.with_opacity(0.1,ft.colors.WHITE),border_radius=10,content_padding=10,label_style=ft.TextStyle(color=APP_TEXT_COLOR_PLACEHOLDER,size=14))],spacing=10),ft.Row([create_custom_textfield("Precio Compra",ref=_prod_pcompra_ref,width=175,keyboard_type=ft.KeyboardType.NUMBER,visible=can_see_purchase_price),create_custom_textfield("Precio Menudeo*",ref=_prod_pmenudeo_ref,width=175,keyboard_type=ft.KeyboardType.NUMBER)],spacing=10),ft.Row([create_custom_textfield("Precio Mayoreo",ref=_prod_pmayoreo_ref,width=175,keyboard_type=ft.KeyboardType.NUMBER),create_custom_textfield("Cant. Mayoreo",ref=_prod_cantmayoreo_ref,width=175,keyboard_type=ft.KeyboardType.NUMBER)],spacing=10),ft.Row([create_custom_textfield("Stock Actual",ref=_prod_stock_ref,width=115,keyboard_type=ft.KeyboardType.NUMBER),create_custom_textfield("Stock Mínimo",ref=_prod_stockmin_ref,width=115,keyboard_type=ft.KeyboardType.NUMBER),create_custom_textfield("Unidad Medida",ref=_prod_unidad_ref,width=110,value="unidad")],spacing=10),ft.Text(ref=_prod_error_ref,color=APP_ERROR_COLOR,visible=False,size=13)],spacing=8,scroll=ft.ScrollMode.ADAPTIVE,tight=True)
        product_dialog_obj=ft.AlertDialog(modal=True,title=ft.Text(ref=_prod_dialog_title_ref,size=20,weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_PRIMARY),content=ft.Container(product_dialog_layout,width=380,height=500 if can_see_purchase_price else 460),actions=[ft.TextButton("Cancelar",on_click=lambda e:close_dialog_global(page,product_dialog_obj)),ft.ElevatedButton("Guardar",on_click=save_product_data,bgcolor=APP_PRIMARY_COLOR,color=APP_TEXT_COLOR_PRIMARY,style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))],shape=ft.RoundedRectangleBorder(radius=15),bgcolor=DIALOG_BG_COLOR)
        def open_product_dialog(prod_data=None):
            nonlocal cat_options_prod_dialog,prov_options_prod_dialog;categorias_list_dlg=controllers.obtener_todas_las_categorias_usuario(current_user_id);cat_options_prod_dialog=[ft.dropdown.Option(str(cat['id']),cat['nombre_categoria'])for cat in categorias_list_dlg if isinstance(cat,dict)and'error'not in cat]if isinstance(categorias_list_dlg,list)else[];_prod_cat_dd_ref.current.options=cat_options_prod_dialog;proveedores_list_dlg=controllers.obtener_todos_los_proveedores_usuario(current_user_id);prov_options_prod_dialog=[ft.dropdown.Option(str(prov['id']),prov['nombre_proveedor'])for prov in proveedores_list_dlg if isinstance(prov,dict)and'error'not in prov]if isinstance(proveedores_list_dlg,list)else[];_prod_prov_dd_ref.current.options=prov_options_prod_dialog;page.dialog=product_dialog_obj;_prod_error_ref.current.visible=False;_prod_pcompra_ref.current.visible=can_see_purchase_price
            if prod_data:
                _current_edit_prod_id_holder["id"]=prod_data['id'];full_prod_details=controllers.obtener_detalles_producto_admin(current_user_id,prod_data['id'])
                if not full_prod_details or'error'in full_prod_details:page.show_snack_bar(ft.SnackBar(ft.Text(f"Error al cargar producto: {full_prod_details.get('error','Desconocido')}"),open=True,bgcolor=APP_ERROR_COLOR));return
                _prod_dialog_title_ref.current.value="Editar Producto";_prod_name_ref.current.value=full_prod_details.get('nombre_producto','');_prod_code_ref.current.value=full_prod_details.get('codigo_barras','');_prod_desc_ref.current.value=full_prod_details.get('descripcion','');_prod_cat_dd_ref.current.value=str(full_prod_details.get('categoria_id'))if full_prod_details.get('categoria_id')else None;_prod_prov_dd_ref.current.value=str(full_prod_details.get('proveedor_id'))if full_prod_details.get('proveedor_id')else None
                if can_see_purchase_price:_prod_pcompra_ref.current.value=str(full_prod_details.get('precio_compra','0.0'))
                _prod_pmenudeo_ref.current.value=str(full_prod_details.get('precio_venta_menudeo','0.0'));_prod_pmayoreo_ref.current.value=str(full_prod_details.get('precio_venta_mayoreo',''))if full_prod_details.get('precio_venta_mayoreo')is not None else"";_prod_cantmayoreo_ref.current.value=str(full_prod_details.get('cantidad_para_mayoreo',''))if full_prod_details.get('cantidad_para_mayoreo')is not None else"";_prod_stock_ref.current.value=str(full_prod_details.get('stock_actual','0'));_prod_stockmin_ref.current.value=str(full_prod_details.get('stock_minimo','0'));_prod_unidad_ref.current.value=full_prod_details.get('unidad_medida','unidad')
            else:
                _current_edit_prod_id_holder["id"]=None;_prod_dialog_title_ref.current.value="Agregar Producto"
                for r_field in[_prod_name_ref,_prod_code_ref,_prod_desc_ref,_prod_pcompra_ref,_prod_pmenudeo_ref,_prod_pmayoreo_ref,_prod_cantmayoreo_ref,_prod_stock_ref,_prod_stockmin_ref,_prod_unidad_ref]:r_field.current.value=""
                _prod_cat_dd_ref.current.value=None;_prod_prov_dd_ref.current.value=None;_prod_unidad_ref.current.value="unidad"
            page.dialog.open=True;page.update()
        def confirm_delete_product(prod_id,prod_name):
            def do_delete_prod(e):
                close_dialog_global(page, page.dialog);res=controllers.eliminar_producto_admin(current_user_id,prod_id)
                if res.get("success"):load_products_table(prod_search_field_ref.current.value if prod_search_field_ref.current else None);page.show_snack_bar(ft.SnackBar(ft.Text(f"Producto '{prod_name}' marcado como inactivo."),open=True,bgcolor=ft.colors.GREEN_ACCENT_700))
                else:page.show_snack_bar(ft.SnackBar(ft.Text(res.get("error","Error.")),open=True,bgcolor=APP_ERROR_COLOR))
            dlg=ft.AlertDialog(modal=True,title=ft.Text("Confirmar Inactivación"),content=ft.Text(f"¿Marcar '{prod_name}' como inactivo?"),actions=[ft.TextButton("No",on_click=lambda e:close_dialog_global(page,dlg)),ft.TextButton("Sí",on_click=do_delete_prod,style=ft.ButtonStyle(color=APP_ERROR_COLOR))]);page.dialog=dlg;dlg.open=True;page.update()
        def open_stock_entry_dialog(prod_id,prod_name):
            _qty_ref=ft.Ref[ft.TextField]();_notes_ref=ft.Ref[ft.TextField]();_stock_error_ref=ft.Ref[ft.Text]()
            def do_add_stock(e):
                _stock_error_ref.current.visible=False;_stock_error_ref.current.update();
                try:qty=int(_qty_ref.current.value);assert qty>0
                except:_stock_error_ref.current.value="Cantidad inválida.";_stock_error_ref.current.visible=True;_stock_error_ref.current.update();return
                res=controllers.registrar_entrada_stock_usuario(current_user_id,prod_id,qty,_notes_ref.current.value)
                if res.get("success"):load_products_table(prod_search_field_ref.current.value if prod_search_field_ref.current else None);close_dialog_global(page, page.dialog);page.show_snack_bar(ft.SnackBar(ft.Text(f"Stock de '{prod_name}' actualizado."),open=True,bgcolor=ft.colors.GREEN_ACCENT_700))
                else:_stock_error_ref.current.value=res.get("error","Error.");_stock_error_ref.current.visible=True;_stock_error_ref.current.update()
            stock_dialog=ft.AlertDialog(modal=True,title=ft.Text(f"Entrada Stock: {prod_name}"),content=ft.Column([create_custom_textfield("Cantidad*",ref=_qty_ref,keyboard_type=ft.KeyboardType.NUMBER,width=320),create_custom_textfield("Notas",ref=_notes_ref,width=320),ft.Text(ref=_stock_error_ref,color=APP_ERROR_COLOR,visible=False,size=13)],tight=True,spacing=10,width=330),actions=[ft.TextButton("Cancelar",on_click=lambda e:close_dialog_global(page,stock_dialog)),ft.ElevatedButton("Registrar",on_click=do_add_stock,bgcolor=APP_PRIMARY_COLOR)],shape=ft.RoundedRectangleBorder(radius=15),bgcolor=DIALOG_BG_COLOR);page.dialog=stock_dialog;stock_dialog.open=True;page.update()
        products_table_ctrl=ft.DataTable(ref=products_datatable_ref,heading_row_color=ft.colors.with_opacity(0.04,ft.colors.WHITE),heading_row_height=38,data_row_min_height=42,data_row_max_height=48,column_spacing=10,expand=True,divider_thickness=0.3,horizontal_lines=ft.border.BorderSide(0.3,ft.colors.with_opacity(0.1,ft.colors.WHITE)),columns=[ft.DataColumn(ft.Text("Cód.",size=11)),ft.DataColumn(ft.Text("Nombre",size=13)),ft.DataColumn(ft.Text("Cat.",size=11)),ft.DataColumn(ft.Text("P.Venta",size=12)),ft.DataColumn(ft.Text("Stock",size=12)),ft.DataColumn(ft.Text("Acciones",size=12))])
        load_products_table()
        return ft.Column([ft.Row([ft.Text("Productos",size=24,weight=ft.FontWeight.BOLD),ft.Row([create_custom_textfield("Buscar...",ref=prod_search_field_ref,width=250,on_submit=lambda e:load_products_table(e.control.value),height=40,content_padding=8,text_size=14,label_size=13,border_radius=8),ft.ElevatedButton("Agregar",icon=ft.icons.ADD,on_click=lambda _:open_product_dialog()if can_manage_inventory else None,disabled=not can_manage_inventory,height=40,style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8),bgcolor=APP_PRIMARY_COLOR,color=APP_TEXT_COLOR_PRIMARY))],spacing=10)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN,vertical_alignment=ft.CrossAxisAlignment.CENTER),ft.Container(products_table_ctrl,expand=True,border=ft.border.all(0.5,FROSTED_GLASS_BORDER_COLOR),border_radius=10,padding=5)],expand=True,spacing=12)

    # --- Sub-vista de Categorías ---
    def get_categories_view():
        cat_datatable_ref=ft.Ref[ft.DataTable]();_cat_name_ref=ft.Ref[ft.TextField]();_cat_desc_ref=ft.Ref[ft.TextField]();_cat_error_ref=ft.Ref[ft.Text]();_cat_edit_id_holder={"id":None};_cat_dialog_title_ref=ft.Ref[ft.Text]()
        def load_cats():
            if cat_datatable_ref.current: cats=controllers.obtener_todas_las_categorias_usuario(current_user_id);cat_datatable_ref.current.rows.clear()
            if isinstance(cats,list):
                for c in cats:cat_datatable_ref.current.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(c['nombre_categoria'],color=APP_TEXT_COLOR_PRIMARY,size=13)),ft.DataCell(ft.Text(c.get('descripcion','')or"-",color=APP_TEXT_COLOR_SECONDARY,size=13,italic=not c.get('descripcion',''))),ft.DataCell(ft.Row([ft.IconButton(ft.icons.EDIT_OUTLINED,icon_size=18,on_click=lambda e,cat=c:open_cat_dialog(cat),disabled=not can_manage_categories),ft.IconButton(ft.icons.DELETE_OUTLINE,icon_size=18,icon_color=APP_ERROR_COLOR,on_click=lambda e,cat_id=c['id'],cat_name=c['nombre_categoria']:confirm_delete_cat(cat_id,cat_name),disabled=not can_manage_categories)],spacing=0)if can_manage_categories else ft.Container())]))
            if cat_datatable_ref.current: cat_datatable_ref.current.update()
        def save_cat(e):
            _cat_error_ref.current.visible=False;name=_cat_name_ref.current.value;desc=_cat_desc_ref.current.value
            if not name:_cat_error_ref.current.value="Nombre es requerido";_cat_error_ref.current.visible=True;_cat_error_ref.current.update();return
            res=controllers.crear_nueva_categoria_admin(current_user_id,name,desc)if _cat_edit_id_holder["id"]is None else controllers.actualizar_categoria_admin(current_user_id,_cat_edit_id_holder["id"],name,desc)
            if res and(res.get("id")or res.get("success")):load_cats();close_dialog_global(page, page.dialog);page.show_snack_bar(ft.SnackBar(ft.Text("Categoría guardada."),open=True,bgcolor=ft.colors.GREEN_ACCENT_700))
            else:_cat_error_ref.current.value=res.get("error","Error");_cat_error_ref.current.visible=True;_cat_error_ref.current.update()
        cat_dialog_obj=ft.AlertDialog(modal=True,title=ft.Text(ref=_cat_dialog_title_ref),content=ft.Column([create_custom_textfield("Nombre*",ref=_cat_name_ref,width=320),create_custom_textfield("Descripción",ref=_cat_desc_ref,width=320,multiline=True,min_lines=2),ft.Text(ref=_cat_error_ref,color=APP_ERROR_COLOR,visible=False)],tight=True,width=330,height=200),actions=[ft.TextButton("Cancelar",on_click=lambda e:close_dialog_global(page,cat_dialog_obj)),ft.ElevatedButton("Guardar",on_click=save_cat)],bgcolor=DIALOG_BG_COLOR)
        def open_cat_dialog(cat=None):
            page.dialog=cat_dialog_obj;_cat_error_ref.current.visible=False;_cat_edit_id_holder["id"]=cat['id']if cat else None
            _cat_dialog_title_ref.current.value="Editar Categoría"if cat else"Nueva Categoría";_cat_name_ref.current.value=cat['nombre_categoria']if cat else"";_cat_desc_ref.current.value=cat.get('descripcion','')if cat else""
            page.dialog.open=True;page.update()
        def confirm_delete_cat(cat_id,cat_name):
            def do_del(e):
                close_dialog_global(page, page.dialog);res=controllers.eliminar_categoria_admin(current_user_id,cat_id)
                if res.get("success"):load_cats();page.show_snack_bar(ft.SnackBar(ft.Text(f"Categoría '{cat_name}' eliminada."),open=True))
                else:page.show_snack_bar(ft.SnackBar(ft.Text(res.get("error","Error")),open=True,bgcolor=APP_ERROR_COLOR))
            dlg=ft.AlertDialog(title=ft.Text("Confirmar"),content=ft.Text(f"Eliminar '{cat_name}'?"),actions=[ft.TextButton("No",on_click=lambda e:close_dialog_global(page,dlg)),ft.TextButton("Sí",on_click=do_del)]);page.dialog=dlg;dlg.open=True;page.update()
        cat_table_ctrl=ft.DataTable(ref=cat_datatable_ref,columns=[ft.DataColumn(ft.Text("Nombre")),ft.DataColumn(ft.Text("Descripción")),ft.DataColumn(ft.Text("Acciones"))],expand=True)
        load_cats()
        return ft.Column([ft.Row([ft.Text("Categorías",size=24),ft.ElevatedButton("Nueva",icon=ft.icons.ADD,on_click=lambda _:open_cat_dialog(),disabled=not can_manage_categories)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),ft.Container(cat_table_ctrl,expand=True,border=ft.border.all(0.5,FROSTED_GLASS_BORDER_COLOR),border_radius=8)],expand=True,spacing=10)

    # --- Sub-vista de Proveedores ---
    def get_providers_view():
        prov_datatable_ref=ft.Ref[ft.DataTable]();_pname,_pcontact,_ptel,_pemail,_paddr,_perror_prov=(ft.Ref[ft.TextField]()for _ in range(5))+(ft.Ref[ft.Text](),);_prov_edit_id_holder={"id":None};_prov_dialog_title_ref=ft.Ref[ft.Text]()
        def load_provs():
            if prov_datatable_ref.current:provs=controllers.obtener_todos_los_proveedores_usuario(current_user_id);prov_datatable_ref.current.rows.clear()
            if isinstance(provs,list):
                for p in provs:prov_datatable_ref.current.rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(p['nombre_proveedor'])),ft.DataCell(ft.Text(p.get('contacto_principal','')or"-")),ft.DataCell(ft.Text(p.get('telefono','')or"-")),ft.DataCell(ft.Row([ft.IconButton(ft.icons.EDIT,icon_size=18,on_click=lambda e,prov=p:open_prov_dialog(prov),disabled=not can_manage_providers),ft.IconButton(ft.icons.DELETE,icon_size=18,icon_color=APP_ERROR_COLOR,on_click=lambda e,p_id=p['id'],p_name=p['nombre_proveedor']:confirm_delete_prov(p_id,p_name),disabled=not can_manage_providers)],spacing=0)if can_manage_providers else ft.Container())]))
            if prov_datatable_ref.current:prov_datatable_ref.current.update()
        def save_prov(e):
            _perror_prov_ref.current.visible=False;data={"nombre_proveedor":_pname.current.value,"contacto_principal":_pcontact.current.value or None,"telefono":_ptel.current.value or None,"email":_pemail.current.value or None,"direccion":_paddr.current.value or None}
            if not data["nombre_proveedor"]:_perror_prov_ref.current.value="Nombre es requerido";_perror_prov_ref.current.visible=True;_perror_prov_ref.current.update();return
            res=controllers.crear_nuevo_proveedor_admin(current_user_id,**data)if _prov_edit_id_holder["id"]is None else controllers.actualizar_proveedor_admin(current_user_id,_prov_edit_id_holder["id"],**data)
            if res and(res.get("id")or res.get("success")):load_provs();close_dialog_global(page, page.dialog);page.show_snack_bar(ft.SnackBar(ft.Text("Proveedor guardado."),open=True))
            else:_perror_prov_ref.current.value=res.get("error","Error");_perror_prov_ref.current.visible=True;_perror_prov_ref.current.update()
        prov_dialog_obj=ft.AlertDialog(modal=True,title=ft.Text(ref=_prov_dialog_title_ref),content=ft.Column([create_custom_textfield("Nombre*",ref=_pname,width=320),create_custom_textfield("Contacto",ref=_pcontact,width=320),create_custom_textfield("Teléfono",ref=_ptel,width=320,keyboard_type=ft.KeyboardType.PHONE),create_custom_textfield("Email",ref=_pemail,width=320,keyboard_type=ft.KeyboardType.EMAIL),create_custom_textfield("Dirección",ref=_paddr,width=320,multiline=True,min_lines=2),ft.Text(ref=_perror_prov_ref,color=APP_ERROR_COLOR,visible=False)],tight=True,width=330,height=380,scroll=ft.ScrollMode.ADAPTIVE),actions=[ft.TextButton("Cancelar",on_click=lambda e:close_dialog_global(page,prov_dialog_obj)),ft.ElevatedButton("Guardar",on_click=save_prov)],bgcolor=DIALOG_BG_COLOR)
        def open_prov_dialog(prov=None):
            page.dialog=prov_dialog_obj;_perror_prov_ref.current.visible=False;_prov_edit_id_holder["id"]=prov['id']if prov else None
            _prov_dialog_title_ref.current.value="Editar Proveedor"if prov else"Nuevo Proveedor";_pname.current.value=prov['nombre_proveedor']if prov else"";_pcontact.current.value=prov.get('contacto_principal','')if prov else"";_ptel.current.value=prov.get('telefono','')if prov else"";_pemail.current.value=prov.get('email','')if prov else"";_paddr.current.value=prov.get('direccion','')if prov else""
            page.dialog.open=True;page.update()
        def confirm_delete_prov(p_id,p_name):
            def do_del(e):
                close_dialog_global(page, page.dialog);res=controllers.eliminar_proveedor_admin(current_user_id,p_id)
                if res.get("success"):load_provs();page.show_snack_bar(ft.SnackBar(ft.Text(f"Proveedor '{p_name}' eliminado."),open=True))
                else:page.show_snack_bar(ft.SnackBar(ft.Text(res.get("error","Error")),open=True,bgcolor=APP_ERROR_COLOR))
            dlg=ft.AlertDialog(title=ft.Text("Confirmar"),content=ft.Text(f"Eliminar '{p_name}'?"),actions=[ft.TextButton("No",on_click=lambda e:close_dialog_global(page,dlg)),ft.TextButton("Sí",on_click=do_del)]);page.dialog=dlg;dlg.open=True;page.update()
        prov_table_ctrl=ft.DataTable(ref=prov_datatable_ref,columns=[ft.DataColumn(ft.Text("Nombre")),ft.DataColumn(ft.Text("Contacto")),ft.DataColumn(ft.Text("Teléfono")),ft.DataColumn(ft.Text("Acciones"))],expand=True)
        load_provs()
        return ft.Column([ft.Row([ft.Text("Proveedores",size=24),ft.ElevatedButton("Nuevo",icon=ft.icons.ADD,on_click=lambda _:open_prov_dialog(),disabled=not can_manage_providers)],alignment=ft.MainAxisAlignment.SPACE_BETWEEN),ft.Container(prov_table_ctrl,expand=True,border=ft.border.all(0.5,FROSTED_GLASS_BORDER_COLOR),border_radius=8)],expand=True,spacing=10)

    # Pestañas
    def on_tabs_change(e):
        idx = e.control.selected_index
        views_map = {0: get_products_view, 1: get_categories_view, 2: get_providers_view}
        perm_map = {0: True, 1: can_manage_categories, 2: can_manage_providers}
        if perm_map.get(idx, False): inventory_tab_content_area.current.content = views_map[idx]()
        else: inventory_tab_content_area.current.content = ft.Column([ft.Icon(ft.icons.LOCK_OUTLINE,size=36),ft.Text("Permiso Denegado",size=20)],expand=True,horizontal_alignment=ft.CrossAxisAlignment.CENTER,alignment=ft.MainAxisAlignment.CENTER)
        inventory_tab_content_area.current.update()

    inventory_tabs_ctrl = ft.Tabs(selected_index=0, on_change=on_tabs_change, tabs=[ ft.Tab(text="Productos", icon=ft.icons.LIST_ALT_ROUNDED), ft.Tab(text="Categorías", icon=ft.icons.CATEGORY_ROUNDED, disabled=not (can_manage_categories or can_manage_inventory)), ft.Tab(text="Proveedores", icon=ft.icons.LOCAL_SHIPPING_ROUNDED, disabled=not (can_manage_providers or can_manage_inventory))], label_color=APP_PRIMARY_COLOR, unselected_label_color=APP_TEXT_COLOR_SECONDARY, indicator_color=APP_PRIMARY_COLOR, height=45, divider_color=ft.colors.with_opacity(0.1,ft.colors.WHITE))
    inventory_tab_content_area.current = ft.Container(content=get_products_view(), expand=True, padding=ft.padding.only(top=12))
    return ft.Column([ft.Text("Gestión de Inventario",size=26,weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_PRIMARY), ft.Divider(height=1,thickness=0.5,color=FROSTED_GLASS_BORDER_COLOR), inventory_tabs_ctrl, inventory_tab_content_area], expand=True,spacing=10)

# --- Vista del Punto de Venta (POS) ---
def create_pos_view(page: ft.Page, view_manager):
    # ... (código de create_pos_view sin cambios significativos, usa close_dialog_global) ...
    current_user_id = page.session.get("user_id")
    carrito_items_ref = ft.Ref[ft.Column](); carrito_data = []
    total_venta_ref = ft.Ref[ft.Text](); cambio_ref = ft.Ref[ft.Text]()
    monto_recibido_field_ref = ft.Ref[ft.TextField](); cliente_nombre_field_ref = ft.Ref[ft.TextField]()
    cliente_id_field_ref = ft.Ref[ft.TextField](); tipo_pago_dd_ref = ft.Ref[ft.Dropdown]()
    search_field_ref = ft.Ref[ft.TextField](); search_results_col_ref = ft.Ref[ft.Column]()
    def actualizar_total_carrito():
        total = sum(item['subtotal'] for item in carrito_data)
        if total_venta_ref.current: total_venta_ref.current.value = f"Total: ${total:.2f}"; total_venta_ref.current.update()
        return total
    def actualizar_vista_carrito():
        if carrito_items_ref.current:
            carrito_items_ref.current.controls.clear()
            for index, item in enumerate(carrito_data):
                carrito_items_ref.current.controls.append(ft.Row([ft.Text(f"{item['nombre_producto']} ({item['cantidad']}x${item['precio_unitario_actual']:.2f})", expand=True, size=13),ft.Text(f"${item['subtotal']:.2f}", size=13),ft.IconButton(ft.icons.REMOVE_CIRCLE_OUTLINE, icon_size=18, on_click=lambda e,idx=index:modificar_cantidad_carrito(idx,-1)),ft.IconButton(ft.icons.ADD_CIRCLE_OUTLINE, icon_size=18, on_click=lambda e,idx=index:modificar_cantidad_carrito(idx,1)),ft.IconButton(ft.icons.DELETE_FOREVER_OUTLINED, icon_size=18,icon_color=APP_ERROR_COLOR,on_click=lambda e,idx=index:eliminar_item_carrito(idx))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=2))
            actualizar_total_carrito(); carrito_items_ref.current.update()
    def anadir_producto_al_carrito(producto_data, cantidad_a_anadir=1):
        if not producto_data or cantidad_a_anadir <= 0: return
        for item in carrito_data:
            if item['producto_id'] == producto_data['id']: item['cantidad'] += cantidad_a_anadir; item['subtotal'] = item['cantidad'] * item['precio_unitario_actual']; actualizar_vista_carrito(); return
        precio_venta = producto_data['precio_venta_menudeo']
        if producto_data.get('cantidad_para_mayoreo') and cantidad_a_anadir >= producto_data['cantidad_para_mayoreo'] and producto_data.get('precio_venta_mayoreo') is not None: precio_venta = producto_data['precio_venta_mayoreo']
        carrito_data.append({'producto_id':producto_data['id'],'nombre_producto':producto_data['nombre_producto'],'cantidad':cantidad_a_anadir,'precio_unitario_actual':precio_venta,'subtotal':cantidad_a_anadir*precio_venta,'stock_disponible_inicial':producto_data['stock_actual']})
        actualizar_vista_carrito()
    def modificar_cantidad_carrito(index_carrito, delta_cantidad):
        item=carrito_data[index_carrito]; nueva_cantidad=item['cantidad']+delta_cantidad
        if nueva_cantidad <=0: eliminar_item_carrito(index_carrito); return
        item['cantidad']=nueva_cantidad; producto_db_info=models.obtener_producto_por_id(item['producto_id'])
        if producto_db_info:
            precio_actualizado=producto_db_info['precio_venta_menudeo']
            if producto_db_info.get('cantidad_para_mayoreo')and nueva_cantidad>=producto_db_info['cantidad_para_mayoreo']and producto_db_info.get('precio_venta_mayoreo')is not None: precio_actualizado=producto_db_info['precio_venta_mayoreo']
            item['precio_unitario_actual']=precio_actualizado
        item['subtotal']=item['cantidad']*item['precio_unitario_actual']; actualizar_vista_carrito()
    def eliminar_item_carrito(index_carrito):
        if 0<=index_carrito<len(carrito_data): del carrito_data[index_carrito]; actualizar_vista_carrito()
    def buscar_producto_pos_handler(e):
        termino = search_field_ref.current.value.strip();
        if search_results_col_ref.current: search_results_col_ref.current.controls.clear()
        if len(termino) < 1:
            if search_results_col_ref.current: search_results_col_ref.current.update(); return
        producto_cb=None
        if termino.isdigit()and len(termino)>5: producto_cb=models.obtener_producto_por_codigo_barras(termino)
        productos_encontrados=([producto_cb]if producto_cb else controllers.obtener_productos_para_vista(current_user_id,nombre_filtro=termino,limit=5))
        if isinstance(productos_encontrados,list)and productos_encontrados:
            for prod in productos_encontrados: search_results_col_ref.current.controls.append(ft.ListTile(title=ft.Text(prod['nombre_producto'],size=13),subtitle=ft.Text(f"Stock:{prod['stock_actual']}|${prod['precio_venta_menudeo']:.2f}",size=11),leading=ft.Icon(ft.icons.ADD_SHOPPING_CART,color=ft.colors.GREEN_300),on_click=lambda _,p=prod:anadir_producto_al_carrito(p),dense=True,content_padding=ft.padding.symmetric(horizontal=8,vertical=0)))
        else: search_results_col_ref.current.controls.append(ft.Text("No encontrado.",size=12,color=APP_TEXT_COLOR_SECONDARY))
        if search_results_col_ref.current: search_results_col_ref.current.update()
        if search_field_ref.current: search_field_ref.current.focus()
    def calcular_cambio_pos(e=None):
        if cambio_ref.current and monto_recibido_field_ref.current and total_venta_ref.current:
            try:
                total_str=total_venta_ref.current.value.replace("Total: $","").strip(); total=float(total_str)
                monto_str=monto_recibido_field_ref.current.value
                if not monto_str: cambio_ref.current.value="Cambio: $0.00"; cambio_ref.current.update(); return
                monto=float(monto_str)
                if monto>=total: cambio_ref.current.value=f"Cambio: ${monto-total:.2f}"
                else: cambio_ref.current.value="Monto insuficiente"
            except: cambio_ref.current.value="Cambio: $0.00"
            cambio_ref.current.update()
    def finalizar_venta_pos_handler(e):
        if not carrito_data: page.show_snack_bar(ft.SnackBar(ft.Text("Carrito vacío."),open=True,bgcolor=APP_ERROR_COLOR)); return
        total_final=actualizar_total_carrito(); monto_rec_val=monto_recibido_field_ref.current.value; monto_rec_float=None
        if monto_rec_val:
            try: monto_rec_float=float(monto_rec_val)
            except ValueError: page.show_snack_bar(ft.SnackBar(ft.Text("Monto recibido inválido."),open=True,bgcolor=APP_ERROR_COLOR)); return
        tipo_pago=tipo_pago_dd_ref.current.value or 'efectivo'
        if tipo_pago=='efectivo'and(monto_rec_float is None or monto_rec_float<total_final): page.show_snack_bar(ft.SnackBar(ft.Text("Monto insuficiente para pago en efectivo."),open=True,bgcolor=APP_ERROR_COLOR)); return
        res_venta=controllers.procesar_nueva_venta_usuario(current_user_id,carrito_data,total_final,cliente_nombre=cliente_nombre_field_ref.current.value or None,cliente_identificacion=cliente_id_field_ref.current.value or None,monto_recibido=monto_rec_float,tipo_pago=tipo_pago)
        if res_venta.get("success"):
            cambio=res_venta.get('cambio',0.00); cambio_s=f"${cambio:.2f}"if cambio is not None else"$0.00"
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Venta #{res_venta['venta_id']} registrada. Cambio:{cambio_s}"),open=True,bgcolor=ft.colors.GREEN_ACCENT_700,duration=3000))
            carrito_data.clear(); actualizar_vista_carrito()
            for field in[monto_recibido_field_ref,cliente_nombre_field_ref,cliente_id_field_ref,search_field_ref]:
                if field.current:field.current.value="";field.current.update()
            if cambio_ref.current:cambio_ref.current.value="Cambio: $0.00";cambio_ref.current.update()
            if tipo_pago_dd_ref.current:tipo_pago_dd_ref.current.value="efectivo";tipo_pago_dd_ref.current.update()
            if search_results_col_ref.current:search_results_col_ref.current.controls.clear();search_results_col_ref.current.update()
            if search_field_ref.current:search_field_ref.current.focus()
        else: page.show_snack_bar(ft.SnackBar(ft.Text(f"Error:{res_venta.get('error','Desconocido')}"),open=True,bgcolor=APP_ERROR_COLOR,duration=4000))
    panel_busqueda = ft.Container(ft.Column([ft.Text("Buscar Producto",weight=ft.FontWeight.BOLD,size=16), create_custom_textfield("Nombre o Código...",ref=search_field_ref,width=None,on_submit=buscar_producto_pos_handler,height=40,dense=True), ft.Container(ft.Column(ref=search_results_col_ref,scroll=ft.ScrollMode.ADAPTIVE,spacing=1),expand=True,border=ft.border.all(0.5,FROSTED_GLASS_BORDER_COLOR),border_radius=8,padding=3,bgcolor=ft.colors.with_opacity(0.03,ft.colors.WHITE))],spacing=6),padding=10,border_radius=10,width=260)
    panel_carrito = ft.Container(ft.Column([ft.Text("Carrito",weight=ft.FontWeight.BOLD,size=18),ft.Divider(height=5),ft.Container(ft.Column(ref=carrito_items_ref,scroll=ft.ScrollMode.ADAPTIVE,spacing=3),expand=True,padding=ft.padding.only(top=3)),ft.Divider(height=5),ft.Text(ref=total_venta_ref,value="Total: $0.00",weight=ft.FontWeight.BOLD,size=20,text_align=ft.TextAlign.RIGHT)],spacing=5),padding=10,border_radius=10,expand=True)
    panel_finalizacion = ft.Container(ft.Column([ft.Text("Finalizar Venta",weight=ft.FontWeight.BOLD,size=16),create_custom_textfield("Cliente(Opc)",ref=cliente_nombre_field_ref,width=None,height=40,dense=True),create_custom_textfield("ID Cliente(Opc)",ref=cliente_id_field_ref,width=None,height=40,dense=True),ft.Dropdown(ref=tipo_pago_dd_ref,label="Pago",value="efectivo",options=[ft.dropdown.Option(k,v)for k,v in{"efectivo":"Efectivo","tarjeta_debito":"Débito","tarjeta_credito":"Crédito","transferencia":"Transferencia","otro":"Otro"}.items()],width=None,height=48,text_style=ft.TextStyle(size=14),bgcolor=ft.colors.with_opacity(0.1,ft.colors.WHITE),border_radius=10,content_padding=10,label_style=ft.TextStyle(size=13)),create_custom_textfield("Monto Recibido",ref=monto_recibido_field_ref,width=None,keyboard_type=ft.KeyboardType.NUMBER,on_change=calcular_cambio_pos,height=40,dense=True),ft.Text(ref=cambio_ref,value="Cambio: $0.00",weight=ft.FontWeight.BOLD,size=18),ft.Container(height=8),ft.ElevatedButton("COBRAR",icon=ft.icons.PAYMENT_ROUNDED,on_click=finalizar_venta_pos_handler,bgcolor=ft.colors.GREEN_ACCENT_700,color=APP_TEXT_COLOR_PRIMARY,width=None,height=45,style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))),ft.TextButton("Cancelar Venta",icon=ft.icons.CANCEL_OUTLINED,on_click=lambda e:(carrito_data.clear(),actualizar_vista_carrito(),monto_recibido_field_ref.current.value(""),calcular_cambio_pos()),style=ft.ButtonStyle(color=APP_ERROR_COLOR),width=None)],spacing=6),padding=10,border_radius=10,width=260)
    return ft.Column([ft.Text("Punto de Venta",size=26,weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_PRIMARY),ft.Divider(height=1,thickness=0.5,color=FROSTED_GLASS_BORDER_COLOR),ft.Row([panel_busqueda,panel_carrito,panel_finalizacion],expand=True,vertical_alignment=ft.CrossAxisAlignment.STRETCH,spacing=10)],expand=True,spacing=10)

# --- Vista de Reportes ---
def create_reports_view(page: ft.Page, view_manager):
    # ... (código de create_reports_view sin cambios significativos, usa close_dialog_global) ...
    current_user_id = page.session.get("user_id")
    report_type_dd_ref = ft.Ref[ft.Dropdown](); date_from_ref = ft.Ref[ft.TextField](); date_to_ref = ft.Ref[ft.TextField](); top_n_field_ref = ft.Ref[ft.TextField](); feedback_area_ref = ft.Ref[ft.Column]()
    def update_filter_visibility(e=None):
        selected_report = report_type_dd_ref.current.value; is_top_products_report = selected_report == "productos_mas_vendidos"
        if top_n_field_ref.current: top_n_field_ref.current.visible = is_top_products_report; top_n_field_ref.current.update()
    def handle_generate_report(e, export_format):
        if not report_type_dd_ref.current.value: page.show_snack_bar(ft.SnackBar(ft.Text("Selecciona un tipo de reporte."),open=True,bgcolor=APP_ERROR_COLOR)); return
        if not date_from_ref.current.value or not date_to_ref.current.value: page.show_snack_bar(ft.SnackBar(ft.Text("Selecciona un rango de fechas."),open=True,bgcolor=APP_ERROR_COLOR)); return
        report_type = report_type_dd_ref.current.value; fecha_inicio = date_from_ref.current.value; fecha_fin = date_to_ref.current.value
        if feedback_area_ref.current: feedback_area_ref.current.controls.clear(); feedback_area_ref.current.update()
        page.show_snack_bar(ft.SnackBar(ft.Text(f"Generando reporte {report_type} en {export_format}..."),open=True, duration=2000)); filepath = None; error_msg = None
        try:
            if report_type == "ventas_periodo":
                data = controllers.generar_reporte_ventas_periodo_ctrl(current_user_id, fecha_inicio, fecha_fin)
                if "error" in data: error_msg = data["error"]
                else: filepath = report_generator.generar_excel_ventas_periodo(data, fecha_inicio, fecha_fin) if export_format == 'excel' else report_generator.generar_pdf_ventas_periodo(data, fecha_inicio, fecha_fin)
            elif report_type == "productos_mas_vendidos":
                top_n_val = top_n_field_ref.current.value
                if not top_n_val or not top_n_val.isdigit() or int(top_n_val) <= 0: error_msg = "Top N debe ser un número positivo."; raise ValueError(error_msg)
                data = controllers.generar_reporte_productos_mas_vendidos_ctrl(current_user_id, fecha_inicio, fecha_fin, int(top_n_val))
                if "error" in data: error_msg = data["error"]
                else: filepath = report_generator.generar_excel_productos_mas_vendidos(data, fecha_inicio, fecha_fin, int(top_n_val)) if export_format == 'excel' else report_generator.generar_pdf_productos_mas_vendidos(data, fecha_inicio, fecha_fin, int(top_n_val))
            elif report_type == "ventas_por_usuario":
                data = controllers.generar_reporte_ventas_por_usuario_ctrl(current_user_id, fecha_inicio, fecha_fin)
                if "error" in data: error_msg = data["error"]
                else: filepath = report_generator.generar_excel_ventas_por_usuario(data, fecha_inicio, fecha_fin) if export_format == 'excel' else report_generator.generar_pdf_ventas_por_usuario(data, fecha_inicio, fecha_fin)
            else: error_msg = "Tipo de reporte no soportado."
        except Exception as ex: error_msg = f"Error inesperado: {ex}"; print(f"Excepción en reporte: {ex}")
        if error_msg: page.show_snack_bar(ft.SnackBar(ft.Text(error_msg),open=True,bgcolor=APP_ERROR_COLOR,duration=4000))
        elif filepath:
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Reporte generado: {filepath}"),open=True,bgcolor=ft.colors.GREEN_ACCENT_700,duration=5000))
            if feedback_area_ref.current: feedback_area_ref.current.controls.append(ft.Text(f"Guardado en: {os.path.abspath(filepath)}",color=APP_TEXT_COLOR_SECONDARY,selectable=True)); feedback_area_ref.current.update()
        else: page.show_snack_bar(ft.SnackBar(ft.Text("Error desconocido al generar."),open=True,bgcolor=APP_ERROR_COLOR,duration=4000))
    hoy_default = datetime.now().strftime("%Y-%m-%d"); hace_7_dias_default = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    report_options_column = ft.Column([ft.Text("Tipo de Reporte:",weight=ft.FontWeight.BOLD), ft.Dropdown(ref=report_type_dd_ref,options=[ft.dropdown.Option("ventas_periodo","Ventas por Período"),ft.dropdown.Option("productos_mas_vendidos","Productos Más Vendidos"),ft.dropdown.Option("ventas_por_usuario","Ventas por Usuario")],width=350,on_change=update_filter_visibility,text_style=ft.TextStyle(color=APP_TEXT_COLOR_PRIMARY),bgcolor=ft.colors.with_opacity(0.1,ft.colors.WHITE),border_radius=8,content_padding=10), ft.Text("Rango de Fechas:",weight=ft.FontWeight.BOLD,margin=ft.margin.only(top=15)), create_custom_textfield("Fecha Desde (YYYY-MM-DD)",ref=date_from_ref,width=170,value=hace_7_dias_default), create_custom_textfield("Fecha Hasta (YYYY-MM-DD)",ref=date_to_ref,width=170,value=hoy_default), create_custom_textfield("Top N Productos:",ref=top_n_field_ref,width=170,value="10",keyboard_type=ft.KeyboardType.NUMBER,visible=False), ft.Container(height=20), ft.Row([ft.ElevatedButton("Generar Excel",icon=ft.icons.TABLE_CHART_OUTLINED,on_click=lambda e:handle_generate_report(e,'excel'),style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_700,color=APP_TEXT_COLOR_PRIMARY,shape=ft.RoundedRectangleBorder(radius=8)),height=40),ft.ElevatedButton("Generar PDF",icon=ft.icons.PICTURE_AS_PDF_OUTLINED,on_click=lambda e:handle_generate_report(e,'pdf'),style=ft.ButtonStyle(bgcolor=ft.colors.RED_700,color=APP_TEXT_COLOR_PRIMARY,shape=ft.RoundedRectangleBorder(radius=8)),height=40)],spacing=15,alignment=ft.MainAxisAlignment.START), ft.Column(ref=feedback_area_ref,spacing=5,margin=ft.margin.only(top=15))],spacing=10,width=400)
    return ft.Column([ft.Text("Generación de Reportes",size=26,weight=ft.FontWeight.BOLD,color=APP_TEXT_COLOR_PRIMARY),ft.Divider(height=1,thickness=0.5,color=FROSTED_GLASS_BORDER_COLOR),ft.Container(content=report_options_column,padding=20,expand=True,alignment=ft.alignment.top_left)],expand=True,spacing=15)

# --- Vista de Configuración (Import/Export DB y Productos) ---
def create_settings_view(page: ft.Page, view_manager):
    current_user_id = page.session.get("user_id")

    # Permisos para esta sección
    can_export_db = models.tiene_permiso(current_user_id, 'exportar_bd')
    can_import_db = models.tiene_permiso(current_user_id, 'importar_bd')
    can_export_prods = models.tiene_permiso(current_user_id, 'exportar_datos_productos')
    can_import_prods = models.tiene_permiso(current_user_id, 'importar_datos_productos')

    results_text_area = ft.Text("", selectable=True, color=APP_TEXT_COLOR_SECONDARY, size=13)

    # --- Exportar DB ---
    def export_db_click(e):
        results_text_area.value = "Exportando base de datos..." ; results_text_area.update()
        result = controllers.exportar_database_completa_ctrl(current_user_id)
        if result.get("success"):
            results_text_area.value = f"Éxito: {result.get('mensaje')}\nRuta: {os.path.abspath(result.get('filepath'))}"
        else:
            results_text_area.value = f"Error: {result.get('error')}"
        results_text_area.update()

    # --- Importar DB ---
    def on_import_db_dialog_result(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            sql_filepath = e.files[0].path

            def confirm_import(e_confirm): # Definida dentro para capturar sql_filepath
                close_dialog_global(page, page.dialog) # Cerrar diálogo de confirmación
                results_text_area.value = f"Importando base de datos desde {sql_filepath}..." ; results_text_area.update()
                # Realizar un backup ANTES de importar
                backup_before_import = db_utils.export_database_to_sql()
                if backup_before_import:
                    results_text_area.value += f"\nBackup previo realizado en: {backup_before_import}"
                else:
                    results_text_area.value += f"\nADVERTENCIA: No se pudo crear backup previo."
                results_text_area.update()

                import_result = controllers.importar_database_desde_sql_ctrl(current_user_id, sql_filepath)
                if import_result.get("success"):
                    results_text_area.value += f"\nÉxito: {import_result.get('mensaje')}"
                    page.show_snack_bar(ft.SnackBar(ft.Text("Importación de DB completada. REINICIE LA APLICACIÓN."), open=True, duration=7000, bgcolor=ft.colors.GREEN_ACCENT_700))
                else:
                    results_text_area.value += f"\nError en importación: {import_result.get('error')}"
                    if backup_before_import:
                        results_text_area.value += f"\nSe recomienda restaurar el backup: {backup_before_import}"
                results_text_area.update()

            confirm_dialog = ft.AlertDialog(
                modal=True, title=ft.Text("Confirmar Importación de Base de Datos", color=APP_TEXT_COLOR_PRIMARY),
                content=ft.Text(f"ADVERTENCIA: Esta acción reemplazará la base de datos actual con el contenido de '{os.path.basename(sql_filepath)}'.\n\n¿Está seguro de que desea continuar? Se recomienda hacer un backup manual primero si no está seguro.", color=APP_TEXT_COLOR_SECONDARY),
                actions=[ft.TextButton("Cancelar", on_click=lambda e: close_dialog_global(page, confirm_dialog)), ft.ElevatedButton("Sí, Importar", on_click=confirm_import, bgcolor=APP_ERROR_COLOR, color=APP_TEXT_COLOR_PRIMARY)],
                shape=ft.RoundedRectangleBorder(radius=15), bgcolor=DIALOG_BG_COLOR
            )
            page.dialog = confirm_dialog; confirm_dialog.open = True; page.update()
        else:
            results_text_area.value = "Importación de DB cancelada o sin archivo seleccionado." ; results_text_area.update()

    file_picker_import_db = ft.FilePicker(on_result=on_import_db_dialog_result)
    page.overlay.append(file_picker_import_db) # Necesario para que FilePicker funcione

    # --- Exportar Productos ---
    def export_products_click(e):
        results_text_area.value = "Exportando productos a Excel..."; results_text_area.update()
        result = controllers.exportar_productos_a_excel_ctrl(current_user_id)
        if result.get("success"):
            results_text_area.value = f"Éxito: {result.get('mensaje')}\nRuta: {os.path.abspath(result.get('filepath'))}"
        else:
            results_text_area.value = f"Error: {result.get('error')}"
        results_text_area.update()

    # --- Importar Productos ---
    def on_import_products_dialog_result(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            excel_filepath = e.files[0].path
            results_text_area.value = f"Importando productos desde {excel_filepath}..." ; results_text_area.update()
            import_result = controllers.importar_productos_desde_excel_ctrl(current_user_id, excel_filepath)

            summary_msg = import_result.get('mensaje', 'Error desconocido en importación.')
            full_feedback = summary_msg
            if import_result.get('detalles'):
                for detalle_fila in import_result.get('detalles'):
                    full_feedback += f"\n  Fila {detalle_fila['fila']}: {detalle_fila['nombre_original']} - {detalle_fila['status']} - {detalle_fila['mensaje']}"
            results_text_area.value = full_feedback
            page.show_snack_bar(ft.SnackBar(ft.Text(summary_msg), open=True, duration=5000, bgcolor=ft.colors.GREEN_ACCENT_700 if import_result.get("success") else APP_ERROR_COLOR))
        else:
            results_text_area.value = "Importación de productos cancelada o sin archivo."
        results_text_area.update()

    file_picker_import_prods = ft.FilePicker(on_result=on_import_products_dialog_result)
    page.overlay.append(file_picker_import_prods)

    return ft.Column(
        [
            ft.Text("Configuración y Utilidades de Datos", size=26, weight=ft.FontWeight.BOLD, color=APP_TEXT_COLOR_PRIMARY),
            ft.Divider(height=1, thickness=0.5, color=FROSTED_GLASS_BORDER_COLOR),
            ft.Container(height=15),

            ft.Text("Base de Datos Completa:", weight=ft.FontWeight.BOLD, size=18, color=APP_TEXT_COLOR_PRIMARY),
            ft.Row([
                ft.ElevatedButton("Exportar DB (.sql)", icon=ft.icons.UPLOAD_FILE, on_click=export_db_click, disabled=not can_export_db, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
                ft.ElevatedButton("Importar DB (.sql)", icon=ft.icons.DOWNLOAD_ROUNDED, on_click=lambda _: file_picker_import_db.pick_files(allow_multiple=False, allowed_extensions=["sql"]), disabled=not can_import_db, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8), bgcolor=APP_ERROR_COLOR if can_import_db else ft.colors.GREY_700)),
            ], spacing=15),
            ft.Text("Nota: La importación de base de datos reemplazará todos los datos actuales. Haga un backup primero.", size=11, color=APP_TEXT_COLOR_SECONDARY, italic=True),
            ft.Container(height=20),

            ft.Text("Datos de Productos:", weight=ft.FontWeight.BOLD, size=18, color=APP_TEXT_COLOR_PRIMARY),
            ft.Row([
                ft.ElevatedButton("Exportar Productos (Excel)", icon=ft.icons.TABLE_ROWS_SHARP, on_click=export_products_click, disabled=not can_export_prods, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
                ft.ElevatedButton("Importar Productos (Excel)", icon=ft.icons.FILE_UPLOAD_OFF_OUTLINED, on_click=lambda _: file_picker_import_prods.pick_files(allow_multiple=False, allowed_extensions=["xlsx"]), disabled=not can_import_prods, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))),
            ], spacing=15),
             ft.Text("Nota: Para importar, el archivo Excel debe tener columnas específicas. Vea la documentación o exporte primero para obtener la plantilla.", size=11, color=APP_TEXT_COLOR_SECONDARY, italic=True),
            ft.Container(height=20),

            ft.Text("Resultados de Operación:", weight=ft.FontWeight.BOLD, size=16, color=APP_TEXT_COLOR_PRIMARY),
            ft.Container(
                content=results_text_area,
                padding=10, border=ft.border.all(1, FROSTED_GLASS_BORDER_COLOR), border_radius=8,
                bgcolor=ft.colors.with_opacity(0.05, ft.colors.WHITE),
                expand=True, # Para que ocupe el espacio restante
                # height=200, # Altura fija si se prefiere
            )
        ],
        expand=True, spacing=10
    )


# --- ViewManager y Main ---
class ViewManager:
    def __init__(self, page: ft.Page):
        self.page = page; self.views = {}; self.current_view_name = None
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER; self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.bgcolor = None
        self.page_container = ft.Container(width=page.window_width, height=page.window_height, expand=True, gradient=ft.LinearGradient(begin=ft.alignment.top_center,end=ft.alignment.bottom_center,colors=[ft.colors.PURPLE_700, ft.colors.BLUE_GREY_800],stops=[0.0,1.0]),padding=0,margin=0)
        self.page.add(self.page_container)

    def add_view(self, name, view_controls_func): self.views[name] = view_controls_func

    def route_to(self, view_name, clear_page_content=True, **kwargs):
        if view_name in self.views:
            self.current_view_name = view_name
            if view_name == "login" or "recover_password" in view_name :
                self.page.appbar = None; self.page.vertical_alignment = ft.MainAxisAlignment.CENTER; self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER; self.page.padding = ft.padding.all(20)
            else:
                self.page.padding = 0
            if clear_page_content and hasattr(self.page_container,'content')and self.page_container.content:
                if isinstance(self.page_container.content,(ft.Column,ft.Row)):
                    # Limpiar controles de Column o Row
                    if hasattr(self.page_container.content, 'controls'):
                        self.page_container.content.controls.clear()
                else: # Si es un solo control, asignarlo a None
                    self.page_container.content = None

            view_content_elements = self.views[view_name](self.page, self, **kwargs) # Pasar self (ViewManager)
            if not isinstance(view_content_elements, list): view_content_elements = [view_content_elements]

            # El dashboard devuelve una Fila, las otras vistas una lista de controles para una Columna
            if view_name == "dashboard":
                view_layout = view_content_elements[0] # Asumir que es la Fila principal
            else:
                view_layout = ft.Column(
                    controls=view_content_elements,
                    alignment=ft.MainAxisAlignment.START if view_name not in ["login", "recover_password_step1", "recover_password_step2", "recover_password_step3"] else ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.START if view_name not in ["login", "recover_password_step1", "recover_password_step2", "recover_password_step3"] else ft.CrossAxisAlignment.CENTER,
                    expand=True, spacing= 0 if view_name == "dashboard" else None # Evitar doble espaciado para dashboard
                )

            self.page_container.content = view_layout; self.page.update(); print(f"Navegando a: {view_name}")
        else: print(f"Error: Vista '{view_name}' no encontrada.")

def main(page: ft.Page):
    page.title = "Punto de Venta Moderno"; page.window_width=1320; page.window_height=780; page.window_resizable=True; page.padding=0
    view_mgr = ViewManager(page)
    view_mgr.add_view("login", create_login_view)
    view_mgr.add_view("dashboard", create_dashboard_view)
    view_mgr.add_view("recover_password_step1", create_recover_pass_step1_view)
    view_mgr.add_view("recover_password_step2", create_recover_pass_step2_view)
    view_mgr.add_view("recover_password_step3", create_recover_pass_step3_view)
    # Las vistas de admin, inventario, pos, reportes y settings se cargan desde el dashboard
    view_mgr.route_to("login")

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets") # Añadido assets_dir por si se usan imágenes/fuentes locales
