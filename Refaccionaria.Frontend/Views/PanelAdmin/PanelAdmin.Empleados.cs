using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;

using System;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Frontend.Models;

namespace Refaccionaria.Frontend.Views;

public sealed partial class PanelAdmin : Page
{
    // =========================================================
    // NUEVO EMPLEADO
    // =========================================================

    private void NuevoEmpleado_Click(
        object sender,
        RoutedEventArgs e)
    {
        modoFormulario = "NuevoEmpleado";

        usuarioEditando = null;
        refaccionEditando = null;

        // Mostrar formulario
        Formulario.Visibility = Visibility.Visible;

        // Mostrar únicamente los campos de empleado
        CamposProducto.Visibility = Visibility.Collapsed;
        CamposEmpleado.Visibility = Visibility.Visible;

        // Título
        TxtTituloFormulario.Text = "Nuevo empleado";

        // Este botón solamente pertenece a productos
        BtnEliminarProducto.Visibility = Visibility.Collapsed;

        // Limpiar campos
        TxtFormEmpNombre.Text = string.Empty;
        TxtFormEmpTelefono.Text = string.Empty;
        TxtFormEmpUsuario.Text = string.Empty;
        TxtFormEmpPassword.PasswordRevealMode =
            PasswordRevealMode.Hidden;
        BtnVerPasswordEmpleado.Content = "👁";

        ChkFormEmpActivo.IsChecked = true;

        // Colocar cursor en nombre
        TxtFormEmpNombre.Focus(FocusState.Programmatic);
    }


    // =========================================================
    // EDITAR EMPLEADO
    // =========================================================

    private void EditarEmpleado_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (sender is Button boton &&
            boton.Tag is Usuario usuario)
        {
            AbrirEmpleadoParaEditar(usuario);
        }
    }


    // =========================================================
    // ABRIR EMPLEADO PARA EDITAR
    // =========================================================

    private void AbrirEmpleadoParaEditar(Usuario usuario)
    {
        modoFormulario = "EditarEmpleado";

        usuarioEditando = usuario;
        refaccionEditando = null;

        // Mostrar formulario
        Formulario.Visibility = Visibility.Visible;

        CamposProducto.Visibility = Visibility.Collapsed;
        CamposEmpleado.Visibility = Visibility.Visible;

        TxtTituloFormulario.Text = "Editar empleado";

        // No mostrar botón de retirar producto
        BtnEliminarProducto.Visibility = Visibility.Collapsed;

        // Cargar datos
        TxtFormEmpNombre.Text =
            usuario.Nombre ?? string.Empty;

        TxtFormEmpTelefono.Text =
            usuario.Telefono ?? string.Empty;

        TxtFormEmpUsuario.Text =
            usuario.NombreUsuario ?? string.Empty;

        TxtFormEmpPassword.PasswordRevealMode =
            PasswordRevealMode.Hidden;

        BtnVerPasswordEmpleado.Content = "👁";

        ChkFormEmpActivo.IsChecked =
            usuario.Activo;

        TxtFormEmpNombre.Focus(FocusState.Programmatic);
    }


    // =========================================================
    // GUARDAR NUEVO EMPLEADO
    // =========================================================

    private async Task GuardarNuevoEmpleadoAsync()
    {
        // =====================================================
        // 1. LEER DATOS
        // =====================================================

        string nombre =
            TxtFormEmpNombre.Text.Trim();

        string telefono =
            TxtFormEmpTelefono.Text.Trim();

        string nombreUsuario =
            TxtFormEmpUsuario.Text.Trim();

        string password =
            TxtFormEmpPassword.Password.Trim();

        bool activo =
            ChkFormEmpActivo.IsChecked == true;


        // =====================================================
        // 2. VALIDAR NOMBRE
        // =====================================================

        if (string.IsNullOrWhiteSpace(nombre))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el nombre completo del empleado."
            );

            TxtFormEmpNombre.Focus(
                FocusState.Programmatic
            );

            return;
        }


        // =====================================================
        // 3. VALIDAR TELÉFONO
        // =====================================================

        if (!string.IsNullOrWhiteSpace(telefono))
        {
            if (telefono.Length != 10 ||
                !telefono.All(char.IsDigit))
            {
                await MostrarMensaje(
                    "Teléfono incorrecto",
                    "El teléfono debe contener exactamente 10 números."
                );

                TxtFormEmpTelefono.Focus(
                    FocusState.Programmatic
                );

                return;
            }
        }


        // =====================================================
        // 4. VALIDAR USUARIO
        // =====================================================

        if (string.IsNullOrWhiteSpace(nombreUsuario))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el nombre de usuario."
            );

            TxtFormEmpUsuario.Focus(
                FocusState.Programmatic
            );

            return;
        }


        // =====================================================
        // 5. VALIDAR CONTRASEÑA
        // =====================================================

        if (string.IsNullOrWhiteSpace(password))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe una contraseña para el empleado."
            );

            TxtFormEmpPassword.Focus(
                FocusState.Programmatic
            );

            return;
        }


        try
        {
            // =================================================
            // 6. CREAR MEDIANTE USUARIOSERVICE
            // =================================================

            Usuario nuevoEmpleado =
                await usuarioService.CrearEmpleadoAsync(
                    nombre,
                    telefono,
                    nombreUsuario,
                    password,
                    activo
                );


            // =================================================
            // 7. ACTUALIZAR TABLA
            // =================================================

            vendedores.Add(
                nuevoEmpleado
            );

            TablaEmpleados.ItemsSource =
                vendedores;

            ActualizarResumenEmpleados();


            // =================================================
            // 8. CERRAR FORMULARIO
            // =================================================

            Formulario.Visibility =
                Visibility.Collapsed;

            modoFormulario =
                string.Empty;

            usuarioEditando =
                null;


            // =================================================
            // 9. CONFIRMACIÓN
            // =================================================

            await MostrarMensaje(
                "Empleado registrado",
                $"El empleado \"{nuevoEmpleado.Nombre}\" fue registrado correctamente."
            );
        }
        catch (Exception ex)
        {
            await MostrarMensaje(
                "No se pudo registrar el empleado",
                ex.Message
            );
        }
    }


    // =========================================================
    // GUARDAR EDICIÓN DE EMPLEADO
    // =========================================================

    private async Task GuardarEdicionEmpleadoAsync()
    {
        // =====================================================
        // 1. COMPROBAR EMPLEADO
        // =====================================================

        if (usuarioEditando == null)
        {
            await MostrarMensaje(
                "Empleado no encontrado",
                "No se encontró el empleado que se desea editar."
            );

            return;
        }


        // =====================================================
        // 2. LEER DATOS
        // =====================================================

        string nombre =
            TxtFormEmpNombre.Text.Trim();

        string telefono =
            TxtFormEmpTelefono.Text.Trim();

        string nombreUsuario =
            TxtFormEmpUsuario.Text.Trim();

        string password =
            TxtFormEmpPassword.Password.Trim();

        bool activo =
            ChkFormEmpActivo.IsChecked == true;


        // =====================================================
        // 3. VALIDAR NOMBRE
        // =====================================================

        if (string.IsNullOrWhiteSpace(nombre))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el nombre completo del empleado."
            );

            TxtFormEmpNombre.Focus(
                FocusState.Programmatic
            );

            return;
        }


        // =====================================================
        // 4. VALIDAR TELÉFONO
        // =====================================================

        if (!string.IsNullOrWhiteSpace(telefono))
        {
            if (telefono.Length != 10 ||
                !telefono.All(char.IsDigit))
            {
                await MostrarMensaje(
                    "Teléfono incorrecto",
                    "El teléfono debe contener exactamente 10 números."
                );

                TxtFormEmpTelefono.Focus(
                    FocusState.Programmatic
                );

                return;
            }
        }


        // =====================================================
        // 5. VALIDAR USUARIO
        // =====================================================

        if (string.IsNullOrWhiteSpace(nombreUsuario))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el nombre de usuario."
            );

            TxtFormEmpUsuario.Focus(
                FocusState.Programmatic
            );

            return;
        }


        // =====================================================
        // 6. VALIDAR CONTRASEÑA
        // =====================================================

        if (string.IsNullOrWhiteSpace(password))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "La contraseña no puede quedar vacía."
            );

            TxtFormEmpPassword.Focus(
                FocusState.Programmatic
            );

            return;
        }


        try
        {
            // =================================================
            // 7. EDITAR MEDIANTE USUARIOSERVICE
            // =================================================

            Usuario empleadoActualizado =
                await usuarioService.EditarEmpleadoAsync(
                    usuarioEditando,
                    nombre,
                    telefono,
                    nombreUsuario,
                    password,
                    activo
                );


            // =================================================
            // 8. ACTUALIZAR COLECCIÓN LOCAL
            // =================================================

            Usuario? empleadoLocal =
                vendedores.FirstOrDefault(
                    u => u.Id == empleadoActualizado.Id
                );

            if (empleadoLocal != null &&
                !ReferenceEquals(
                    empleadoLocal,
                    empleadoActualizado))
            {
                int indice =
                    vendedores.IndexOf(
                        empleadoLocal
                    );

                vendedores[indice] =
                    empleadoActualizado;
            }


            // =================================================
            // 9. REFRESCAR TABLA
            // =================================================

            TablaEmpleados.ItemsSource = null;

            TablaEmpleados.ItemsSource =
                vendedores;

            ActualizarResumenEmpleados();


            // =================================================
            // 10. GUARDAR NOMBRE PARA MENSAJE
            // =================================================

            string empleadoNombre =
                empleadoActualizado.Nombre;


            // =================================================
            // 11. CERRAR FORMULARIO
            // =================================================

            usuarioEditando =
                null;

            modoFormulario =
                string.Empty;

            Formulario.Visibility =
                Visibility.Collapsed;


            // =================================================
            // 12. CONFIRMACIÓN
            // =================================================

            await MostrarMensaje(
                "Empleado actualizado",
                $"Los datos de \"{empleadoNombre}\" fueron actualizados."
            );
        }
        catch (Exception ex)
        {
            await MostrarMensaje(
                "No se pudo actualizar el empleado",
                ex.Message
            );
        }
    }


    // =========================================================
    // ELIMINAR EMPLEADO
    // =========================================================

    private async void EliminarEmpleado_Click(
     object sender,
     RoutedEventArgs e)
    {
        // =====================================================
        // 1. OBTENER EMPLEADO
        // =====================================================

        if (sender is not Button boton ||
            boton.Tag is not Usuario usuario)
        {
            return;
        }


        // =====================================================
        // 2. COMPROBAR ESTADO
        // =====================================================

        if (!usuario.Activo)
        {
            await MostrarMensaje(
                "Empleado inactivo",
                $"\"{usuario.Nombre}\" ya se encuentra desactivado."
            );

            return;
        }


        // =====================================================
        // 3. CONFIRMAR DESACTIVACIÓN
        // =====================================================

        ContentDialog dialogo = new()
        {
            Title = "Desactivar empleado",

            Content =
                $"¿Deseas desactivar a \"{usuario.Nombre}\"?\n\n" +
                "El empleado seguirá registrado, pero ya no podrá iniciar sesión.",

            PrimaryButtonText = "Desactivar",
            CloseButtonText = "Cancelar",

            DefaultButton =
                ContentDialogButton.Close,

            XamlRoot = XamlRoot
        };


        ContentDialogResult resultado =
            await dialogo.ShowAsync();


        if (resultado != ContentDialogResult.Primary)
        {
            return;
        }


        try
        {
            // =================================================
            // 4. DESACTIVAR MEDIANTE USUARIOSERVICE
            // =================================================

            Usuario empleadoActualizado =
                await usuarioService.DesactivarEmpleadoAsync(
                    usuario.Id
                );


            // =================================================
            // 5. ACTUALIZAR COLECCIÓN LOCAL
            // =================================================

            Usuario? empleadoLocal =
                vendedores.FirstOrDefault(
                    u => u.Id == empleadoActualizado.Id
                );

            if (empleadoLocal != null &&
                !ReferenceEquals(
                    empleadoLocal,
                    empleadoActualizado))
            {
                int indice =
                    vendedores.IndexOf(
                        empleadoLocal
                    );

                vendedores[indice] =
                    empleadoActualizado;
            }


            // =================================================
            // 6. ACTUALIZAR RESUMEN
            // =================================================

            ActualizarResumenEmpleados();


            // =================================================
            // 7. REFRESCAR TABLA
            // =================================================

            TablaEmpleados.ItemsSource = null;

            TablaEmpleados.ItemsSource =
                vendedores;


            // =================================================
            // 8. CONFIRMACIÓN
            // =================================================

            await MostrarMensaje(
                "Empleado desactivado",
                $"\"{empleadoActualizado.Nombre}\" fue desactivado correctamente."
            );
        }
        catch (Exception ex)
        {
            await MostrarMensaje(
                "No se pudo desactivar el empleado",
                ex.Message
            );
        }
    }

    // =========================================================
    // ACTIVAR / DESACTIVAR EMPLEADO
    // =========================================================

    private async void InterruptorActivo_Click(
    object sender,
    RoutedEventArgs e)
    {
        // =====================================================
        // 1. OBTENER EMPLEADO
        // =====================================================

        if (sender is not CheckBox check ||
            check.Tag is not Usuario usuario)
        {
            return;
        }


        // =====================================================
        // 2. OBTENER NUEVO ESTADO
        // =====================================================

        bool nuevoEstado =
            check.IsChecked == true;


        try
        {
            // =================================================
            // 3. CAMBIAR ESTADO MEDIANTE USUARIOSERVICE
            // =================================================

            Usuario empleadoActualizado =
                await usuarioService.CambiarEstadoAsync(
                    usuario.Id,
                    nuevoEstado
                );


            // =================================================
            // 4. ACTUALIZAR COLECCIÓN LOCAL
            // =================================================

            Usuario? empleadoLocal =
                vendedores.FirstOrDefault(
                    u => u.Id == empleadoActualizado.Id
                );

            if (empleadoLocal != null &&
                !ReferenceEquals(
                    empleadoLocal,
                    empleadoActualizado))
            {
                int indice =
                    vendedores.IndexOf(
                        empleadoLocal
                    );

                vendedores[indice] =
                    empleadoActualizado;
            }


            // =================================================
            // 5. ACTUALIZAR RESUMEN
            // =================================================

            ActualizarResumenEmpleados();


            // =================================================
            // 6. REFRESCAR TABLA
            // =================================================

            TablaEmpleados.ItemsSource = null;

            TablaEmpleados.ItemsSource =
                vendedores;
        }
        catch (Exception ex)
        {
            // =================================================
            // 7. SI FALLA, RECUPERAR EL ESTADO REAL
            // =================================================

            try
            {
                await repoUsuarios.ReloadAsync();

                vendedores.Clear();

                foreach (Usuario empleado in
                    await repoUsuarios.GetAllAsync())
                {
                    if (empleado.Rol.Equals(
                            "Vendedor",
                            StringComparison.OrdinalIgnoreCase))
                    {
                        vendedores.Add(
                            empleado
                        );
                    }
                }

                TablaEmpleados.ItemsSource = null;

                TablaEmpleados.ItemsSource =
                    vendedores;

                ActualizarResumenEmpleados();
            }
            catch
            {
                
            }


            await MostrarMensaje(
                "No se pudo cambiar el estado",
                ex.Message
            );
        }
    }


    // =========================================================
    // DOBLE CLIC EN EMPLEADO
    // =========================================================

    private void TablaEmpleados_DoubleTapped(
        object sender,
        DoubleTappedRoutedEventArgs e)
    {
        if (TablaEmpleados.SelectedItem
            is Usuario usuario)
        {
            AbrirEmpleadoParaEditar(usuario);
        }
    }

    // =========================================================
    // MOSTRAR / OCULTAR CONTRASEÑA DEL EMPLEADO
    // =========================================================
    private void VerPasswordEmpleado_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (TxtFormEmpPassword.PasswordRevealMode ==
            PasswordRevealMode.Hidden)
        {
            TxtFormEmpPassword.PasswordRevealMode =
                PasswordRevealMode.Visible;

            BtnVerPasswordEmpleado.Content = "🙈";
        }
        else
        {
            TxtFormEmpPassword.PasswordRevealMode =
                PasswordRevealMode.Hidden;

            BtnVerPasswordEmpleado.Content = "👁";
        }
    }

    // =========================================================
    // ACTUALIZAR TEXTO DE RESUMEN
    // =========================================================

    private void ActualizarResumenEmpleados()
    {
        int total =
            vendedores.Count;

        int activos =
            vendedores.Count(u => u.Activo);


        TxtResumenEmpleados.Text =
            total == 1
                ? $"1 empleado registrado · {activos} activo"
                : $"{total} empleados registrados · {activos} activos";
    }
}

