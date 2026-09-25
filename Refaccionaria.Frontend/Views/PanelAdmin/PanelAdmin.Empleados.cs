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
        string nombre =
            TxtFormEmpNombre.Text.Trim();

        string telefono =
            TxtFormEmpTelefono.Text.Trim();

        string nombreUsuario =
            TxtFormEmpUsuario.Text.Trim();

        string password =
            TxtFormEmpPassword.Password.Trim();


        // -----------------------------------------------------
        // VALIDAR NOMBRE
        // -----------------------------------------------------

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


        // -----------------------------------------------------
        // VALIDAR TELÉFONO
        // -----------------------------------------------------

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


        // -----------------------------------------------------
        // VALIDAR USUARIO
        // -----------------------------------------------------

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


        // -----------------------------------------------------
        // USUARIO DUPLICADO
        // -----------------------------------------------------

        bool usuarioExiste =
            vendedores.Any(u =>
                u.NombreUsuario.Equals(
                    nombreUsuario,
                    StringComparison.OrdinalIgnoreCase
                )
            );

        if (usuarioExiste)
        {
            await MostrarMensaje(
                "Usuario existente",
                "Ya existe un empleado con ese nombre de usuario."
            );

            TxtFormEmpUsuario.Focus(
                FocusState.Programmatic
            );

            return;
        }


        // -----------------------------------------------------
        // CONTRASEÑA
        // -----------------------------------------------------

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


        // -----------------------------------------------------
        // CREAR EMPLEADO
        // -----------------------------------------------------

        Usuario nuevoEmpleado = new()
        {
            Nombre = nombre,
            Telefono = telefono,
            NombreUsuario = nombreUsuario,
            Password = password,
            Rol = "Vendedor",
            Activo = ChkFormEmpActivo.IsChecked == true
        };


        // -----------------------------------------------------
        // GUARDAR EN usuarios.json
        // -----------------------------------------------------

        await repoUsuarios.AddAsync(nuevoEmpleado);


        // -----------------------------------------------------
        // ACTUALIZAR TABLA
        // -----------------------------------------------------

        vendedores.Add(nuevoEmpleado);

        TablaEmpleados.ItemsSource = vendedores;

        ActualizarResumenEmpleados();


        // -----------------------------------------------------
        // CERRAR FORMULARIO
        // -----------------------------------------------------

        Formulario.Visibility =
            Visibility.Collapsed;

        modoFormulario =
            string.Empty;

        usuarioEditando =
            null;


        await MostrarMensaje(
            "Empleado registrado",
            $"El empleado \"{nombre}\" fue registrado correctamente."
        );
    }


    // =========================================================
    // GUARDAR EDICIÓN DE EMPLEADO
    // =========================================================

    private async Task GuardarEdicionEmpleadoAsync()
    {
        if (usuarioEditando == null)
            return;


        string nombre =
            TxtFormEmpNombre.Text.Trim();

        string telefono =
            TxtFormEmpTelefono.Text.Trim();

        string nombreUsuario =
            TxtFormEmpUsuario.Text.Trim();

        string password =
            TxtFormEmpPassword.Password.Trim();


        // -----------------------------------------------------
        // NOMBRE
        // -----------------------------------------------------

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


        // -----------------------------------------------------
        // TELÉFONO
        // -----------------------------------------------------

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


        // -----------------------------------------------------
        // USUARIO
        // -----------------------------------------------------

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


        // -----------------------------------------------------
        // EVITAR USUARIO DUPLICADO
        // -----------------------------------------------------

        bool usuarioExiste =
            vendedores.Any(u =>
                u.Id != usuarioEditando.Id &&
                u.NombreUsuario.Equals(
                    nombreUsuario,
                    StringComparison.OrdinalIgnoreCase
                )
            );

        if (usuarioExiste)
        {
            await MostrarMensaje(
                "Usuario existente",
                "Ya existe otro empleado con ese nombre de usuario."
            );

            TxtFormEmpUsuario.Focus(
                FocusState.Programmatic
            );

            return;
        }


        // -----------------------------------------------------
        // CONTRASEÑA
        // -----------------------------------------------------

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


        // -----------------------------------------------------
        // ACTUALIZAR
        // -----------------------------------------------------

        usuarioEditando.Nombre =
            nombre;

        usuarioEditando.Telefono =
            telefono;

        usuarioEditando.NombreUsuario =
            nombreUsuario;

        usuarioEditando.Password =
            password;

        usuarioEditando.Rol =
            "Vendedor";

        usuarioEditando.Activo =
            ChkFormEmpActivo.IsChecked == true;


        // -----------------------------------------------------
        // GUARDAR EN JSON
        // -----------------------------------------------------

        await repoUsuarios.UpdateAsync(
            usuarioEditando
        );


        // -----------------------------------------------------
        // REFRESCAR TABLA
        // -----------------------------------------------------

        TablaEmpleados.ItemsSource = null;
        TablaEmpleados.ItemsSource = vendedores;

        ActualizarResumenEmpleados();


        string empleadoActualizado =
            usuarioEditando.Nombre;


        // -----------------------------------------------------
        // CERRAR
        // -----------------------------------------------------

        usuarioEditando = null;

        modoFormulario =
            string.Empty;

        Formulario.Visibility =
            Visibility.Collapsed;


        await MostrarMensaje(
            "Empleado actualizado",
            $"Los datos de \"{empleadoActualizado}\" fueron actualizados."
        );
    }


    // =========================================================
    // ELIMINAR EMPLEADO
    // =========================================================

    private async void EliminarEmpleado_Click(
    object sender,
    RoutedEventArgs e)
    {
        if (sender is not Button boton ||
            boton.Tag is not Usuario usuario)
        {
            return;
        }

        // Si ya está inactivo, no hacemos nada
        if (!usuario.Activo)
        {
            await MostrarMensaje(
                "Empleado inactivo",
                $"\"{usuario.Nombre}\" ya se encuentra desactivado."
            );

            return;
        }

        ContentDialog dialogo = new()
        {
            Title = "Desactivar empleado",

            Content =
                $"¿Deseas desactivar a \"{usuario.Nombre}\"?\n\n" +
                "El empleado seguirá registrado, pero ya no podrá iniciar sesión.",

            PrimaryButtonText = "Desactivar",
            CloseButtonText = "Cancelar",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = XamlRoot
        };

        ContentDialogResult resultado =
            await dialogo.ShowAsync();

        if (resultado != ContentDialogResult.Primary)
            return;

        // SOLO DESACTIVAR.
        // NO eliminar del repositorio.
        usuario.Activo = false;

        // Guardar el cambio en usuarios.json
        await repoUsuarios.UpdateAsync(usuario);

        // Actualizar contador
        ActualizarResumenEmpleados();

        // Refrescar visualmente la tabla.
        // El empleado permanece en vendedores.
        TablaEmpleados.ItemsSource = null;
        TablaEmpleados.ItemsSource = vendedores;

        await MostrarMensaje(
            "Empleado desactivado",
            $"\"{usuario.Nombre}\" fue desactivado correctamente."
        );
    }

    // =========================================================
    // ACTIVAR / DESACTIVAR EMPLEADO
    // =========================================================

    private async void InterruptorActivo_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (sender is not CheckBox check ||
            check.Tag is not Usuario usuario)
        {
            return;
        }


        bool nuevoEstado =
            check.IsChecked == true;


        usuario.Activo =
            nuevoEstado;


        await repoUsuarios.UpdateAsync(
            usuario
        );


        ActualizarResumenEmpleados();

        //Refrescar tabla para actualizar Activo / Inactivo

        TablaEmpleados.ItemsSource = null;
        TablaEmpleados.ItemsSource = vendedores;
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

