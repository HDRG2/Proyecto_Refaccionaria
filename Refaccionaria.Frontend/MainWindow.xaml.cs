using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

using Microsoft.Extensions.DependencyInjection;

using System;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;
using Refaccionaria.Frontend.Views;

namespace Refaccionaria.Frontend
{
    public sealed partial class MainWindow : Window
    {
        // =========================================================
        // VARIABLES
        // =========================================================

        private bool _esAdministrador = false;

        private UIElement? _contenidoLogin;


        // =========================================================
        // REPOSITORIO DE USUARIOS
        // =========================================================

        private readonly IRepository<Usuario> repoUsuarios =
            App.Current.Services
                .GetRequiredService<IRepository<Usuario>>();


        // =========================================================
        // CONSTRUCTOR
        // =========================================================

        public MainWindow()
        {
            InitializeComponent();

            _contenidoLogin = Content;


            // -----------------------------------------------------
            // TAMAÑO DE LA VENTANA
            // -----------------------------------------------------

            IntPtr hwnd =
                WinRT.Interop.WindowNative.GetWindowHandle(this);

            var windowId =
                Microsoft.UI.Win32Interop
                    .GetWindowIdFromWindow(hwnd);

            var appWindow =
                Microsoft.UI.Windowing.AppWindow
                    .GetFromWindowId(windowId);

            appWindow.Resize(
                new Windows.Graphics.SizeInt32(
                    1180,
                    720
                )
            );


            CampoUsuario.Focus(
                FocusState.Programmatic
            );
        }


        // =========================================================
        // SELECCIONAR MOSTRADOR
        // =========================================================

        private void BotonRolMostrador_Click(
            object sender,
            RoutedEventArgs e)
        {
            _esAdministrador = false;

            var recursos =
                ((FrameworkElement)Content).Resources;

            BotonRolMostrador.Style =
                (Style)recursos["BotonRolActivo"];

            BotonRolAdministrador.Style =
                (Style)recursos["BotonRolInactivo"];

            OcultarError();
        }


        // =========================================================
        // SELECCIONAR ADMINISTRADOR
        // =========================================================

        private void BotonRolAdministrador_Click(
            object sender,
            RoutedEventArgs e)
        {
            _esAdministrador = true;

            var recursos =
                ((FrameworkElement)Content).Resources;

            BotonRolAdministrador.Style =
                (Style)recursos["BotonRolActivo"];

            BotonRolMostrador.Style =
                (Style)recursos["BotonRolInactivo"];

            OcultarError();
        }


        // =========================================================
        // MOSTRAR / OCULTAR CONTRASEÑA
        // =========================================================

        private void BotonVerClave_Click(
            object sender,
            RoutedEventArgs e)
        {
            bool estabaOculta =
                CampoClaveVisible.Visibility !=
                Visibility.Visible;


            if (estabaOculta)
            {
                CampoClaveVisible.Text =
                    CampoClave.Password;

                CampoClave.Visibility =
                    Visibility.Collapsed;

                CampoClaveVisible.Visibility =
                    Visibility.Visible;

                CampoClaveVisible.Focus(
                    FocusState.Programmatic
                );

                CampoClaveVisible.SelectionStart =
                    CampoClaveVisible.Text.Length;

                BotonVerClave.Content =
                    "Ocultar";
            }
            else
            {
                CampoClave.Password =
                    CampoClaveVisible.Text;

                CampoClaveVisible.Visibility =
                    Visibility.Collapsed;

                CampoClave.Visibility =
                    Visibility.Visible;

                CampoClave.Focus(
                    FocusState.Programmatic
                );

                BotonVerClave.Content =
                    "Mostrar";
            }
        }


        // =========================================================
        // OBTENER CONTRASEÑA ESCRITA
        // =========================================================

        private string ClaveEscrita()
        {
            return
                CampoClaveVisible.Visibility ==
                Visibility.Visible

                    ? CampoClaveVisible.Text
                    : CampoClave.Password;
        }


        // =========================================================
        // INICIAR SESIÓN
        // =========================================================

        private async void BotonEntrar_Click(
            object sender,
            RoutedEventArgs e)
        {
            string nombreUsuario =
                CampoUsuario.Text.Trim();

            string clave =
                ClaveEscrita();


            // -----------------------------------------------------
            // VALIDAR CAMPOS
            // -----------------------------------------------------

            if (string.IsNullOrWhiteSpace(nombreUsuario))
            {
                MostrarError(
                    "Escribe tu usuario para continuar."
                );

                CampoUsuario.Focus(
                    FocusState.Programmatic
                );

                return;
            }


            if (string.IsNullOrWhiteSpace(clave))
            {
                MostrarError(
                    "Escribe tu contraseña para continuar."
                );

                CampoClave.Focus(
                    FocusState.Programmatic
                );

                return;
            }


            OcultarError();


            BotonEntrar.IsEnabled =
                false;

            BotonEntrar.Content =
                "Entrando…";


            try
            {
                // -------------------------------------------------
                // BUSCAR USUARIO EN usuarios.json
                // -------------------------------------------------

                var usuarios =
                    await repoUsuarios.GetAllAsync();


                Usuario? usuarioEncontrado =
                    usuarios.FirstOrDefault(
                        u =>
                            u.NombreUsuario.Equals(
                                nombreUsuario,
                                StringComparison.OrdinalIgnoreCase
                            )
                    );


                // -------------------------------------------------
                // USUARIO NO EXISTE
                // -------------------------------------------------

                if (usuarioEncontrado == null)
                {
                    MostrarError(
                        "El usuario o la contraseña son incorrectos."
                    );

                    RestaurarBotonEntrar();

                    return;
                }


                // -------------------------------------------------
                // CONTRASEÑA INCORRECTA
                // -------------------------------------------------

                if (usuarioEncontrado.Password != clave)
                {
                    MostrarError(
                        "El usuario o la contraseña son incorrectos."
                    );

                    RestaurarBotonEntrar();

                    return;
                }


                // -------------------------------------------------
                // USUARIO DESACTIVADO
                // -------------------------------------------------

                if (!usuarioEncontrado.Activo)
                {
                    MostrarError(
                        "Este usuario está desactivado. " +
                        "Contacta al administrador."
                    );

                    RestaurarBotonEntrar();

                    return;
                }


                // -------------------------------------------------
                // NORMALIZAR ROL
                // -------------------------------------------------

                string rolUsuario =
                    usuarioEncontrado.Rol?.Trim()
                    ?? string.Empty;


                bool usuarioEsAdministrador =
                    rolUsuario.Equals(
                        "Administrador",
                        StringComparison.OrdinalIgnoreCase
                    );


                bool usuarioEsVendedor =
                    rolUsuario.Equals(
                        "Vendedor",
                        StringComparison.OrdinalIgnoreCase
                    ) ||
                    rolUsuario.Equals(
                        "Mostrador",
                        StringComparison.OrdinalIgnoreCase
                    );


                // -------------------------------------------------
                // ROL NO RECONOCIDO
                // -------------------------------------------------

                if (!usuarioEsAdministrador &&
                    !usuarioEsVendedor)
                {
                    MostrarError(
                        "La cuenta no tiene un rol válido."
                    );

                    RestaurarBotonEntrar();

                    return;
                }


                // =================================================
                // INTENTA ENTRAR COMO ADMINISTRADOR
                // =================================================

                if (_esAdministrador)
                {
                    // ---------------------------------------------
                    // SOLO ADMINISTRADORES PUEDEN ENTRAR
                    // ---------------------------------------------

                    if (!usuarioEsAdministrador)
                    {
                        MostrarError(
                            "Este usuario no tiene permisos " +
                            "de administrador."
                        );

                        RestaurarBotonEntrar();

                        return;
                    }


                    // ---------------------------------------------
                    // BIENVENIDA
                    // ---------------------------------------------

                    await MostrarBienvenida(
                        usuarioEncontrado,
                        "Administrador"
                    );


                    // ---------------------------------------------
                    // PANEL ADMINISTRADOR
                    // ---------------------------------------------

                    Content =
                        new PanelAdmin(
                            usuarioEncontrado.NombreUsuario
                        );

                    return;
                }


                // =================================================
                // INTENTA ENTRAR COMO MOSTRADOR
                // =================================================

                if (!usuarioEsVendedor)
                {
                    MostrarError(
                        "Esta cuenta es de administrador. " +
                        "Selecciona Administrador para iniciar sesión."
                    );

                    RestaurarBotonEntrar();

                    return;
                }


                // -------------------------------------------------
                // BIENVENIDA
                // -------------------------------------------------

                await MostrarBienvenida(
                    usuarioEncontrado,
                    "Mostrador"
                );


                // -------------------------------------------------
                // PANTALLA DE VENTAS
                // -------------------------------------------------

                Content =
                    new VentaPage();
            }
            catch (Exception ex)
            {
                MostrarError(
                    "No se pudo iniciar sesión: " +
                    ex.Message
                );

                RestaurarBotonEntrar();
            }
        }


        // =========================================================
        // MENSAJE DE BIENVENIDA
        // =========================================================

        private async Task MostrarBienvenida(
            Usuario usuario,
            string rol)
        {
            ContentDialog dialogo =
                new()
                {
                    Title = "El Pistón",

                    Content =
                        $"Bienvenido, {usuario.Nombre}.\n" +
                        $"Rol: {rol}",

                    CloseButtonText =
                        "Aceptar",

                    XamlRoot =
                        Content.XamlRoot
                };


            await dialogo.ShowAsync();
        }


        // =========================================================
        // RESTAURAR BOTÓN DE ENTRADA
        // =========================================================

        private void RestaurarBotonEntrar()
        {
            BotonEntrar.IsEnabled =
                true;

            BotonEntrar.Content =
                "Entrar al sistema";
        }


        // =========================================================
        // MOSTRAR ERROR
        // =========================================================

        private void MostrarError(string texto)
        {
            TextoError.Text =
                texto;

            CajaError.Visibility =
                Visibility.Visible;
        }


        // =========================================================
        // OCULTAR ERROR
        // =========================================================

        private void OcultarError()
        {
            CajaError.Visibility =
                Visibility.Collapsed;
        }


        // =========================================================
        // CERRAR SESIÓN
        // =========================================================

        public void CerrarSesion()
        {
            if (_contenidoLogin == null)
                return;


            // -----------------------------------------------------
            // REGRESAR AL LOGIN
            // -----------------------------------------------------

            Content =
                _contenidoLogin;


            // -----------------------------------------------------
            // MOSTRADOR POR DEFECTO
            // -----------------------------------------------------

            _esAdministrador =
                false;


            var recursos =
                ((FrameworkElement)Content).Resources;


            BotonRolMostrador.Style =
                (Style)recursos["BotonRolActivo"];


            BotonRolAdministrador.Style =
                (Style)recursos["BotonRolInactivo"];


            // -----------------------------------------------------
            // LIMPIAR CAMPOS
            // -----------------------------------------------------

            CampoUsuario.Text =
                string.Empty;


            CampoClave.Password =
                string.Empty;


            CampoClaveVisible.Text =
                string.Empty;


            // -----------------------------------------------------
            // OCULTAR CONTRASEÑA VISIBLE
            // -----------------------------------------------------

            CampoClaveVisible.Visibility =
                Visibility.Collapsed;


            CampoClave.Visibility =
                Visibility.Visible;


            BotonVerClave.Content =
                "Mostrar";


            // -----------------------------------------------------
            // LIMPIAR ERRORES
            // -----------------------------------------------------

            OcultarError();


            // -----------------------------------------------------
            // RESTAURAR BOTÓN
            // -----------------------------------------------------

            RestaurarBotonEntrar();


            // -----------------------------------------------------
            // FOCO
            // -----------------------------------------------------

            CampoUsuario.Focus(
                FocusState.Programmatic
            );
        }
    }
}