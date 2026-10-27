using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Controls.Primitives;

using Microsoft.Extensions.DependencyInjection;

using System;
using System.Linq;
using System.Threading.Tasks;
using System.Text.RegularExpressions;

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
            
            // Usuario del login: solo letras y números
            Validaciones.LetrasYNumeros(CampoUsuario);
            
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

                        // -----------------------------------------------------
            // LOGO DE LA BARRA SUPERIOR
            // -----------------------------------------------------

            appWindow.SetIcon(
                System.IO.Path.Combine(
                    AppContext.BaseDirectory,
                    "Assets",
                    "LogoPiston.ico"
                )
            );

            // -----------------------------------------------------
            // COLORES DE LA BARRA SUPERIOR
            // -----------------------------------------------------

            var barra = appWindow.TitleBar;

            var grisBarra =
                Microsoft.UI.ColorHelper.FromArgb(255, 0x2B, 0x2B, 0x2B);

            var grisBoton =
                Microsoft.UI.ColorHelper.FromArgb(255, 0x3D, 0x3D, 0x3D);

            var amarillo =
                Microsoft.UI.ColorHelper.FromArgb(255, 0xFF, 0xC1, 0x07);

            var blanco =
                Microsoft.UI.ColorHelper.FromArgb(255, 0xFF, 0xFF, 0xFF);

            // Fondo gris y letras amarillas
            barra.BackgroundColor = grisBarra;
            barra.InactiveBackgroundColor = grisBarra;
            barra.ForegroundColor = amarillo;
            barra.InactiveForegroundColor = amarillo;

            // Botones de minimizar, maximizar y cerrar
            barra.ButtonBackgroundColor = grisBarra;
            barra.ButtonInactiveBackgroundColor = grisBarra;
            barra.ButtonForegroundColor = blanco;
            barra.ButtonHoverBackgroundColor = grisBoton;
            barra.ButtonHoverForegroundColor = blanco;
            barra.ButtonPressedBackgroundColor = grisBoton;
            barra.ButtonPressedForegroundColor = amarillo;

            CampoUsuario.Focus(
                FocusState.Programmatic
            );
        }


        private void LayoutLogin_SizeChanged(
            object sender,
            SizeChangedEventArgs e)
        {
            bool ventanaEstrecha = e.NewSize.Width < 900;

            PanelLogo.Visibility = ventanaEstrecha
                ? Visibility.Collapsed
                : Visibility.Visible;

            ColumnaLogo.Width = ventanaEstrecha
                ? new GridLength(0)
                : new GridLength(1.15, GridUnitType.Star);

            ColumnaFormulario.Width =
                new GridLength(1, GridUnitType.Star);
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
        // ENTRAR CON LA TECLA ENTER
        // =========================================================

        private void CampoLogin_KeyDown(
            object sender,
            KeyRoutedEventArgs e)
        {
            if (e.Key != Windows.System.VirtualKey.Enter)
                return;

            e.Handled = true;

            // Si ya se está validando un inicio de sesión,
            // no se vuelve a intentar.
            if (!BotonEntrar.IsEnabled)
                return;

            BotonEntrar_Click(
                BotonEntrar,
                new RoutedEventArgs()
            );
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
                    new VentaPage(usuarioEncontrado);
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

    // =============================================================
    // VALIDACIONES
    // =============================================================
    // Aquí están juntas todas las reglas de "qué se puede escribir"
    // en las cajas de texto del programa.
    //
    // Cada pantalla solo dice qué regla usa cada caja, por ejemplo:
    //
    //     Validaciones.SoloLetras(TxtFormEmpNombre);
    //
    // Si el usuario escribe algo que no se acepta, la letra no
    // aparece y se muestra un aviso debajo de la caja.
    // =============================================================
    public static class Validaciones
    {
        // =========================================================
        // MENSAJES
        // =========================================================

        private const string AvisoLetras =
            "Solo se aceptan letras. No se aceptan números ni caracteres especiales.";

        private const string AvisoNumeros =
            "Solo se aceptan números. No se aceptan letras ni caracteres especiales.";

        private const string AvisoLetrasNumeros =
            "Solo se aceptan letras y números. No se aceptan caracteres especiales.";

        private const string AvisoCodigo =
            "Solo se aceptan letras, números y guion (-).";

        private const string AvisoBusqueda =
            "Solo se aceptan letras y números. No se aceptan caracteres especiales.";

        private const string AvisoNombrePieza =
            "Solo se aceptan letras, números, espacios y los signos - / . ( ) ,";

        private const string AvisoModeloAuto =
            "Solo se aceptan letras, números, espacios, guion (-) y punto (.)";

        private const string AvisoPrecio =
            "Solo se aceptan números y un punto decimal (máximo 2 decimales).";


        // =========================================================
        // REGLAS
        // =========================================================

        // Letras (incluye acentos y ñ) y espacios
        public static bool EsLetras(string texto) =>
            texto.All(c => char.IsLetter(c) || c == ' ');

        // Solo dígitos del 0 al 9
        public static bool EsNumeros(string texto) =>
            texto.All(c => c >= '0' && c <= '9');

        // Letras y números, sin espacios
        public static bool EsLetrasNumeros(string texto) =>
            texto.All(c => char.IsLetter(c) || (c >= '0' && c <= '9'));

        // Letras, números y guion (ej. FIL-001). ÚNICA regla con guion.
        public static bool EsCodigo(string texto) =>
            texto.All(c => char.IsLetter(c) || (c >= '0' && c <= '9') || c == '-');

        // Letras, números y espacios (sin guion)
        public static bool EsBusqueda(string texto) =>
            texto.All(c => char.IsLetter(c) || (c >= '0' && c <= '9') || c == ' ');

        // Nombre de una pieza: letras, números, espacios y los signos
        // que se usan en refacciones (ej. "Llanta 205/55 R16",
        // "Aceite 5W-30", "Bujía (iridio)", "Foco H4 12V, 55W").
        public static bool EsNombrePieza(string texto) =>
            texto.All(c =>
                char.IsLetter(c) ||
                (c >= '0' && c <= '9') ||
                c == ' ' || c == '-' || c == '/' ||
                c == '.' || c == '(' || c == ')' || c == ',');

        // Modelo de auto: letras, números, espacios, guion y punto
        // (ej. "X-Trail", "CR-V", "CX-5", "F-150", "Serie 3").
        public static bool EsModeloAuto(string texto) =>
            texto.All(c =>
                char.IsLetter(c) ||
                (c >= '0' && c <= '9') ||
                c == ' ' || c == '-' || c == '.');

        // Números con un punto y máximo 2 decimales (ej. 159.50)
        public static bool EsPrecio(string texto) =>
            Regex.IsMatch(texto, @"^[0-9]*(\.[0-9]{0,2})?$");


        // =========================================================
        // CONECTAR CAJAS CON SU REGLA
        // =========================================================

        public static void SoloLetras(TextBox caja) =>
            Aplicar(caja, EsLetras, AvisoLetras);

        public static void SoloNumeros(TextBox caja) =>
            Aplicar(caja, EsNumeros, AvisoNumeros);

        public static void LetrasYNumeros(TextBox caja) =>
            Aplicar(caja, EsLetrasNumeros, AvisoLetrasNumeros);

        public static void Codigo(TextBox caja) =>
            Aplicar(caja, EsCodigo, AvisoCodigo);

        public static void Busqueda(TextBox caja) =>
            Aplicar(caja, EsBusqueda, AvisoBusqueda);

        public static void NombrePieza(TextBox caja) =>
            Aplicar(caja, EsNombrePieza, AvisoNombrePieza);

        public static void ModeloAuto(TextBox caja) =>
            Aplicar(caja, EsModeloAuto, AvisoModeloAuto);

        public static void Precio(TextBox caja) =>
            Aplicar(caja, EsPrecio, AvisoPrecio);


        // ---------------------------------------------------------
        // Cada caja tiene UN solo globito y UN solo temporizador.
        // Si el usuario sigue presionando teclas no permitidas, no
        // se crean más globitos: solo se reinician los 2 segundos.
        // ---------------------------------------------------------

        private static void Aplicar(
            TextBox caja,
            Func<string, bool> regla,
            string aviso)
        {
            ToolTip globo = new()
            {
                Content = aviso,
                Placement = PlacementMode.Bottom
            };

            var temporizador =
                caja.DispatcherQueue.CreateTimer();

            temporizador.Interval =
                TimeSpan.FromSeconds(2);

            temporizador.IsRepeating =
                false;


            // Quita el globito
            void Ocultar()
            {
                temporizador.Stop();

                globo.IsOpen = false;

                ToolTipService.SetToolTip(caja, null);
            }


            // Se quita a los 2 segundos, al salir de la caja
            // o al cambiar de pantalla
            temporizador.Tick += (t, a) => Ocultar();
            caja.LostFocus += (s, e) => Ocultar();
            caja.Unloaded += (s, e) => Ocultar();


            caja.BeforeTextChanging += (sender, e) =>
            {
                // Si el programa llena la caja (por ejemplo al abrir
                // "Editar"), no se bloquea.
                if (caja.FocusState == FocusState.Unfocused)
                    return;

                if (regla(e.NewText))
                    return;

                e.Cancel = true;

                // Mostrar el globito y reiniciar los 2 segundos
                ToolTipService.SetToolTip(caja, globo);

                globo.IsOpen = true;

                temporizador.Stop();
                temporizador.Start();
            };
        }


        // =========================================================
        // REVISIONES AL GUARDAR
        // =========================================================

        public static string? RevisarContrasena(string password)
        {
            if (password.Length < 8)
                return "La contraseña debe tener mínimo 8 caracteres.";

            if (!password.Any(char.IsLetter))
                return "La contraseña debe tener al menos una letra.";

            bool tieneEspecial =
                password.Any(c =>
                    !char.IsLetterOrDigit(c) &&
                    !char.IsWhiteSpace(c));

            if (!tieneEspecial)
                return "Hace falta mínimo un carácter especial en la contraseña " +
                       "(por ejemplo: ! @ # $ % & * ?).";

            return null;
        }


        public static string? RevisarEmpleado(
            string nombre,
            string nombreUsuario,
            string password)
        {
            if (!EsLetras(nombre))
                return "El nombre solo puede tener letras. " +
                       "No se aceptan números ni caracteres especiales.";

            if (!EsLetrasNumeros(nombreUsuario))
                return "El usuario solo puede tener letras y números, sin espacios " +
                       "ni caracteres especiales.";

            return RevisarContrasena(password);
        }


        public static string? RevisarProducto(
            string nombre,
            string codigo)
        {
            if (!EsNombrePieza(nombre))
                return "El nombre de la pieza solo puede tener letras, números, " +
                       "espacios y los signos - / . ( ) ,";

            // "205/55" solo no dice qué pieza es: debe llevar alguna letra.
            if (!nombre.Any(char.IsLetter))
                return "El nombre de la pieza debe incluir al menos una letra " +
                       "(por ejemplo: Llanta 205/55 R16).";

            if (!EsCodigo(codigo))
                return "El código solo puede tener letras, números y guion (-).";

            return null;
        }
    }
    
}