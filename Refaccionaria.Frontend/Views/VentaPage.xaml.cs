using Microsoft.Extensions.DependencyInjection;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using Microsoft.UI.Xaml.Media;
using Microsoft.UI.Xaml.Media.Animation;

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;
using Refaccionaria.Frontend.Services;

namespace Refaccionaria.Frontend.Views
{
    public sealed partial class VentaPage : Page
    {
        // =========================================================
        // REPOSITORIOS
        // =========================================================

        private readonly IRepository<Refaccion> repoRefacciones =
            App.Current.Services.GetRequiredService<IRepository<Refaccion>>();

        private readonly IRepository<Marca> repoMarcas =
            App.Current.Services.GetRequiredService<IRepository<Marca>>();

        private readonly IRepository<Categoria> repoCategorias =
            App.Current.Services.GetRequiredService<IRepository<Categoria>>();

        private readonly IRepository<ModeloAuto> repoAutos =
            App.Current.Services.GetRequiredService<IRepository<ModeloAuto>>();

        private readonly IRepository<Venta> repoVentas =
            App.Current.Services.GetRequiredService<IRepository<Venta>>();

        private readonly IRepository<DetalleVenta> repoDetalleVentas =
            App.Current.Services.GetRequiredService<IRepository<DetalleVenta>>();

        private readonly Usuario _usuarioActual;

        private readonly VentaService ventaService;

        // =========================================================
        // COLECCIONES
        // =========================================================

        private readonly ObservableCollection<Refaccion> _resultados =
            new();

        private readonly ObservableCollection<DetalleVenta> _ticket =
            new();

        private List<Refaccion> _refacciones = new();
        private List<Marca> _marcas = new();
        private List<Categoria> _categorias = new();
        private List<ModeloAuto> _autos = new();


        // =========================================================
        // CONSTANTES
        // =========================================================

        private const string TODAS_MARCAS =
            "Cualquier marca";

        private const string TODOS_MODELOS =
            "Cualquier modelo";

        private const double ANCHO_PANEL =
            380;


        // =========================================================
        // ESTADO
        // =========================================================

        private string _tipoSeleccionado =
            "Todos";

        private bool _listo = false;

        private bool _panelAbierto = false;

        private decimal _subtotal = 0m;
        private decimal _iva = 0m;
        private decimal _total = 0m;

        private string _metodoPago =
            "Efectivo";


        // =========================================================
        // EVENTO
        // =========================================================

        public event Action<int>? TicketActualizado;


        // =========================================================
        // CONSTRUCTOR
        // =========================================================

        public VentaPage(Usuario usuarioActual)
        {

            InitializeComponent();

            // Buscador: letras, números y guion
            Validaciones.Busqueda(TxtBuscar);

            // Dinero recibido: números y punto decimal
            Validaciones.Precio(TxtRecibido);

            ventaService = new VentaService(
                repoVentas,
                repoDetalleVentas,
                repoRefacciones
            );

            ListaRefacciones.ItemsSource =
                _resultados;

            ListaTicket.ItemsSource =
                _ticket;

            Loaded += VentaPage_Loaded;

            _usuarioActual = usuarioActual;


        }

        // =========================================================
        // LOADED
        // =========================================================

        private async void VentaPage_Loaded(
            object sender,
            RoutedEventArgs e)
        {
            Loaded -= VentaPage_Loaded;


            bool datosCorrectos = await CargarDatosAsync();

            if (!datosCorrectos)
            {
                _listo = false;
                return;
            }

            _listo = true;

            AplicarFiltros();

            ActualizarTotales();
        }


        // =========================================================
        // CARGAR DATOS
        // =========================================================

        private async Task<bool> CargarDatosAsync()
        {
            try
            {
                // -------------------------------------------------
                // REFACCIONES
                // -------------------------------------------------

                await repoRefacciones.ReloadAsync();

                _refacciones =
                    (await repoRefacciones.GetAllAsync())
                    .ToList();


                // -------------------------------------------------
                // MARCAS
                // -------------------------------------------------
                await repoMarcas.ReloadAsync();

                _marcas =
                    (await repoMarcas.GetAllAsync())
                    .ToList();


                // -------------------------------------------------
                // CATEGORÍAS
                // -------------------------------------------------
                await repoCategorias.ReloadAsync();
                _categorias =
                    (await repoCategorias.GetAllAsync())
                    .ToList();


                // -------------------------------------------------
                // AUTOS
                // -------------------------------------------------
                await repoAutos.ReloadAsync();
                _autos =
                    (await repoAutos.GetAllAsync())
                    .ToList();


                ValidarRelacionesDatos();
                // -------------------------------------------------
                // COMPLETAR INFORMACIÓN VISUAL
                // -------------------------------------------------

                foreach (Refaccion refaccion in _refacciones)
                {
                    CompletarDatosRefaccion(
                        refaccion
                    );
                }


                // -------------------------------------------------
                // COMBOBOX
                // -------------------------------------------------

                LlenarMarcas();

                LlenarModelos();

                LlenarAnios();

                return true;
            }
            catch (Exception ex)
            {
                await MostrarMensaje(
                    "Problema en los datos",
                    "Se detectó un problema en los archivos del sistema.\n\n" +
                    ex.Message +
                    "\n\n" +
                    "No es posible iniciar el sistema de ventas.\n" +
                    "Contacta al administrador para restaurar los datos."
                );

                Application.Current.Exit();

                return false;
            }
        }

        // =========================================================
        // VALIDAR RELACIONES ENTRE LOS ARCHIVOS JSON
        // =========================================================

        private void ValidarRelacionesDatos()
        {
            // -------------------------------------------------
            // IDs EXISTENTES
            // -------------------------------------------------

            HashSet<int> idsMarcas =
                _marcas
                .Select(m => m.Id)
                .ToHashSet();

            HashSet<int> idsCategorias =
                _categorias
                .Select(c => c.Id)
                .ToHashSet();

            HashSet<int> idsAutos =
                _autos
                .Select(a => a.Id)
                .ToHashSet();


            // -------------------------------------------------
            // VALIDAR REFACCIONES
            // -------------------------------------------------

            foreach (Refaccion refaccion in _refacciones)
            {
                // MARCA
                if (!idsMarcas.Contains(refaccion.MarcaId))
                {
                    throw new InvalidDataException(
                        $"La refacción '{refaccion.Nombre}' " +
                        $"({refaccion.Codigo}) tiene MarcaId " +
                        $"{refaccion.MarcaId}, pero esa marca " +
                        $"no existe en marcas.json."
                    );
                }


                // CATEGORÍA
                if (!idsCategorias.Contains(refaccion.CategoriaId))
                {
                    throw new InvalidDataException(
                        $"La refacción '{refaccion.Nombre}' " +
                        $"({refaccion.Codigo}) tiene CategoriaId " +
                        $"{refaccion.CategoriaId}, pero esa categoría " +
                        $"no existe en categorias.json."
                    );
                }


                // AUTOS COMPATIBLES
                if (refaccion.AutosCompatibles != null)
                {
                    foreach (int autoId in refaccion.AutosCompatibles)
                    {
                        if (!idsAutos.Contains(autoId))
                        {
                            throw new InvalidDataException(
                                $"La refacción '{refaccion.Nombre}' " +
                                $"({refaccion.Codigo}) contiene AutoId " +
                                $"{autoId}, pero ese vehículo " +
                                $"no existe en autos.json."
                            );
                        }
                    }
                }
            }
        }


        // =========================================================
        // COMPLETAR INFORMACIÓN DEL PRODUCTO
        // =========================================================

        private void CompletarDatosRefaccion(
            Refaccion refaccion)
        {
            Marca? marca =
                _marcas.FirstOrDefault(
                    m => m.Id == refaccion.MarcaId
                );

            Categoria? categoria =
                _categorias.FirstOrDefault(
                    c => c.Id == refaccion.CategoriaId
                );


            refaccion.MarcaNombre =
                marca?.Nombre ?? "Sin marca";

            refaccion.CategoriaNombre =
                categoria?.Nombre ?? "Sin categoría";


            refaccion.AutosDescripciones.Clear();


            if (refaccion.EsUniversal)
            {
                return;
            }


            if (refaccion.AutosCompatibles == null)
            {
                return;
            }


            foreach (int autoId in refaccion.AutosCompatibles)
            {
                ModeloAuto? auto =
                    _autos.FirstOrDefault(
                        a => a.Id == autoId
                    );

                if (auto != null)
                {
                    refaccion.AutosDescripciones.Add(
                        auto.DescripcionCompleta
                    );
                }
            }
        }

        // =========================================================
        // CERRAR SESIÓN
        // =========================================================

        private async void CerrarSesion_Click(
        object sender,
        RoutedEventArgs e)
        {
            ContentDialog dialogo = new()
            {
                Title = "Cerrar sesión",
                Content = "¿Deseas cerrar la sesión actual y regresar al inicio?",
                PrimaryButtonText = "Cerrar sesión",
                CloseButtonText = "Cancelar",
                DefaultButton = ContentDialogButton.Close,
                XamlRoot = XamlRoot
            };

            ContentDialogResult resultado = await dialogo.ShowAsync();

            if (resultado != ContentDialogResult.Primary)
                return;

            // Limpiar carrito
            _ticket.Clear();
            ActualizarTotales();

            // Cerrar panel del ticket
            CerrarTicket();

            // Cerrar ventana de cobro si estaba abierta
            CancelarSimulacion();
            CapaCobro.Visibility = Visibility.Collapsed;

            // Regresar al login
            App.Current.MainWindow?.CerrarSesion();
        }


        // =========================================================
        // MENSAJES
        // =========================================================

        private async Task MostrarMensaje(
            string titulo,
            string mensaje)
        {
            ContentDialog dialogo =
                new()
                {
                    Title =
                        titulo,

                    Content =
                        mensaje,

                    CloseButtonText =
                        "Aceptar",

                    XamlRoot =
                        XamlRoot
                };


            await dialogo.ShowAsync();
        }

        // =========================================================
        // CHATBOT IA - EL PISTÓN
        // =========================================================

        private static readonly HttpClient clienteIA = new HttpClient();

        private bool chatbotOcupado = false;

        private Border? burbujaEscribiendo;
        private DispatcherTimer? temporizadorEscritura;
        private int pasoAnimacion = 0;
        private readonly List<(string Rol, string Texto)> historialChat = new();
        private const int MAX_MENSAJES_HISTORIAL = 20;
        private string? codigoProductoSeleccionado = null;
        private List<string> codigosProductosContexto = new();
        private int paginaActualContexto = 1;

        // ABRIR CHATBOT
        private void AbrirChatbot_Click(
            object sender,
            RoutedEventArgs e)
        {
            PanelChatbot.Visibility =
                PanelChatbot.Visibility == Visibility.Visible
                    ? Visibility.Collapsed
                    : Visibility.Visible;

            if (PanelChatbot.Visibility == Visibility.Visible)
            {
                TxtMensajeChatbot.Focus(FocusState.Programmatic);
            }
        }

        // CERRAR CHATBOT
        private void CerrarChatbot_Click(
            object sender,
            RoutedEventArgs e)
        {
            PanelChatbot.Visibility = Visibility.Collapsed;
        }

        // ENVIAR CON ENTER
        private void TxtMensajeChatbot_KeyDown(
            object sender,
            KeyRoutedEventArgs e)
        {
            if (e.Key == Windows.System.VirtualKey.Enter)
            {
                e.Handled = true;
                EnviarMensajeIAAsync();
            }
        }

        // BOTÓN ENVIAR
        private void EnviarChatbot_Click(
            object sender,
            RoutedEventArgs e)
        {
            EnviarMensajeIAAsync();
        }

        // =========================================================
        // NUEVA CONVERSACIÓN
        // =========================================================

        private void NuevaConversacion_Click(
            object sender,
            RoutedEventArgs e)
        {
            // Evitar reiniciar mientras la IA responde.
            if (chatbotOcupado)
                return;

            // Limpiar la conversación visible.
            PanelMensajes.Children.Clear();

            // Limpiar el historial enviado a la IA.
            historialChat.Clear();

            // Reiniciar el contexto de productos.
            codigoProductoSeleccionado = null;
            codigosProductosContexto.Clear();

            // Limpiar la caja de texto.
            TxtMensajeChatbot.Text = string.Empty;

            // Mostrar nuevamente el mensaje de bienvenida.
            AgregarMensajeChatbot(
                "Asistente IA",
                "¡Hola! Soy el asistente de El Pistón. ¿En qué puedo ayudarte?",
                false
            );

            TxtMensajeChatbot.Focus(FocusState.Programmatic);
        }

        // ENVIAR PREGUNTA A GEMINI
        private async void EnviarMensajeIAAsync()
        {
            if (chatbotOcupado)
                return;

            string pregunta = TxtMensajeChatbot.Text.Trim();

            if (string.IsNullOrWhiteSpace(pregunta))
                return;

            chatbotOcupado = true;

            BtnEnviarChatbot.IsEnabled = false;
            TxtMensajeChatbot.IsEnabled = false;

            // Mostrar el mensaje del usuario
            AgregarMensajeChatbot("Tú", pregunta, true);

            TxtMensajeChatbot.Text = string.Empty;

            try
            {
                // Mostrar los puntitos mientras Gemini responde
                MostrarEscribiendo();

                // Consultar Gemini
                string respuesta = await ConsultarOpenAIAsync(pregunta);

                // Quitar los puntitos
                OcultarEscribiendo();

                // Mostrar la respuesta
                AgregarMensajeChatbot(
                    "Asistente IA",
                    respuesta,
                    false);
            }
            catch (Exception ex)
            {
                // Quitar los puntitos si ocurre un error
                OcultarEscribiendo();

                AgregarMensajeChatbot(
                    "Sistema",
                    "No se pudo consultar la IA.\n\n" + ex.Message,
                    false);
            }
            finally
            {
                // Asegurarnos de detener la animación
                OcultarEscribiendo();

                chatbotOcupado = false;

                BtnEnviarChatbot.IsEnabled = true;
                TxtMensajeChatbot.IsEnabled = true;

                TxtMensajeChatbot.Focus(FocusState.Programmatic);
            }
        }

        // CREAR BURBUJAS DE MENSAJES
        private void AgregarMensajeChatbot(
            string remitente,
            string mensaje,
            bool esUsuario)
        {
            var colorFondo = esUsuario
                ? Windows.UI.Color.FromArgb(255, 217, 4, 41)
                : Windows.UI.Color.FromArgb(255, 229, 229, 229);

            var colorTexto = esUsuario
                ? Microsoft.UI.Colors.White
                : Microsoft.UI.Colors.Black;

            // Preparar el texto del mensaje.
            string contenido = esUsuario
                ? mensaje
                : LimpiarFormatoGemini(mensaje);

            // Evitar mostrar "Asistente IA:" en el saludo inicial.
            bool esBienvenida =
                contenido.StartsWith(
                    "¡Hola! Soy el asistente de El Pistón",
                    StringComparison.OrdinalIgnoreCase);

            if (!esUsuario && !esBienvenida)
            {
                contenido = remitente + ":\n" + contenido;
            }

            TextBlock textoMensaje = new TextBlock
            {
                Text = contenido,
                TextWrapping = TextWrapping.Wrap,
                Foreground = new SolidColorBrush(colorTexto),
                FontSize = 14,
                MaxWidth = 270,

                //Permitir seleccionar y copiar el texto del chatbot
                IsTextSelectionEnabled = true,
                
                // Conservar saltos de línea y mejorar legibilidad.
                LineHeight = 22,
                LineStackingStrategy = LineStackingStrategy.BlockLineHeight
            };

            Border burbuja = new Border
            {
                Background = new SolidColorBrush(colorFondo),
                CornerRadius = new CornerRadius(12),
                Padding = new Thickness(14),
                Margin = new Thickness(0, 0, 0, 10),
                MaxWidth = 298,
                VerticalAlignment = VerticalAlignment.Top,

                HorizontalAlignment = esUsuario
                    ? HorizontalAlignment.Right
                    : HorizontalAlignment.Left,

                Child = textoMensaje
            };

            PanelMensajes.Children.Add(burbuja);

            ScrollChatbot.UpdateLayout();

            ScrollChatbot.ChangeView(
                null,
                ScrollChatbot.ScrollableHeight,
                null);
        }

        // =====================================================
        // LIMPIAR FORMATO DE LAS RESPUESTAS DE GEMINI
        // =====================================================

        private string LimpiarFormatoGemini(string mensaje)
        {
            if (string.IsNullOrWhiteSpace(mensaje))
                return string.Empty;

            string texto = mensaje;

            // Eliminar marcas de negritas y cursivas
            texto = texto.Replace("**", "");
            texto = texto.Replace("__", "");

            // Eliminar encabezados Markdown
            texto = System.Text.RegularExpressions.Regex.Replace(
                texto,
                @"(?m)^\s{0,3}#{1,6}\s+",
                ""
            );

            // Convertir listas Markdown en viñetas
            texto = System.Text.RegularExpressions.Regex.Replace(
                texto,
                @"(?m)^\s*[-*]\s+",
                "• "
            );

            // Evitar demasiados saltos de línea
            texto = System.Text.RegularExpressions.Regex.Replace(
                texto,
                @"\n{3,}",
                "\n\n"
            );

            return texto.Trim();
        }

        // =====================================================
        // CONEXIÓN IA LOCAL
        // =====================================================
        private async Task<string> ConsultarOpenAIAsync(string pregunta)
        {
            // Consultar siempre el inventario actualizado
            string inventarioActual =
                await ObtenerInventarioActualizadoParaIAAsync();

            // Marcas, categorías y autos registrados, aunque todavía no
            // tengan productos ("Ultra 8", "Ford Focus"). Así el asistente
            // también los reconoce.
            var catalogoActual =
                await ObtenerCatalogoParaIAAsync();

            System.IO.File.WriteAllText(
                System.IO.Path.Combine(
                    System.IO.Path.GetTempPath(),
                    "inventario_autogen_debug.json"
                ),
                inventarioActual
            );

            // Enviar la conversación anterior para conservar el contexto
            var historial = historialChat
                .Select(m => new
                {
                    rol = m.Rol,
                    texto = m.Texto
                })
                .ToList();

            var datos = new
            {
                pregunta = pregunta,
                inventario = inventarioActual,
                historial = historial,
                catalogo = catalogoActual,

                contexto = new
                {
                    codigo_seleccionado = codigoProductoSeleccionado,
                    codigos_lista = codigosProductosContexto,
                    pagina_actual = paginaActualContexto
                }
            };

            string json = JsonSerializer.Serialize(datos);

            using var contenido = new StringContent(
                json,
                Encoding.UTF8,
                "application/json"
            );


            string resultado;

            try
            {
                using var tiempoLimite = new CancellationTokenSource(
                    TimeSpan.FromSeconds(60)
                );

                using var respuesta = await clienteIA.PostAsync(
                    "http://127.0.0.1:8000/consultar",
                    contenido,
                    tiempoLimite.Token
                );

                resultado = await respuesta.Content.ReadAsStringAsync(
                    tiempoLimite.Token
                );

                if (!respuesta.IsSuccessStatusCode)
                {
                    if (respuesta.StatusCode ==
                        System.Net.HttpStatusCode.ServiceUnavailable ||
                        respuesta.StatusCode ==
                        System.Net.HttpStatusCode.BadGateway)
                    {
                        return (
                            "El servicio de inteligencia artificial no está " +
                            "disponible en este momento. Verifica que Ollama " +
                            "esté encendido e inténtalo nuevamente."
                        );
                    }

                    return (
                        $"El servidor de IA respondió con un error " +
                        $"({(int)respuesta.StatusCode}). " +
                        "Inténtalo nuevamente."
                    );
                }
            }
            catch (OperationCanceledException)
            {
                return (
                    "La inteligencia artificial tardó demasiado en responder. " +
                    "Verifica que Ollama y el servidor estén funcionando " +
                    "e inténtalo nuevamente."
                );
            }
            catch (HttpRequestException)
            {
                return (
                    "No se pudo conectar con el servidor de inteligencia " +
                    "artificial de El Pistón. Verifica que FastAPI " +
                    "esté encendido e inténtalo nuevamente."
                );
            }


            using var documento = JsonDocument.Parse(resultado);

            string respuestaIA = documento.RootElement
                .GetProperty("respuesta")
                .GetString() ?? "";

            if (string.IsNullOrWhiteSpace(respuestaIA))
            {
                throw new Exception("AutoGen no devolvió una respuesta.");
            }

            // ============================================
            // RECIBIR CONTEXTO CONVERSACIONAL DESDE PYTHON
            // ============================================

            if (documento.RootElement.TryGetProperty(
                    "contexto", out JsonElement contextoRespuesta)
                && contextoRespuesta.ValueKind == JsonValueKind.Object)
            {
                // Recuperar el código seleccionado
                if (contextoRespuesta.TryGetProperty(
                        "codigo_seleccionado", out JsonElement codigo)
                    && (codigo.ValueKind == JsonValueKind.String
                        || codigo.ValueKind == JsonValueKind.Null))
                {
                    codigoProductoSeleccionado = codigo.GetString();
                }

                // Recuperar la lista de productos
                if (contextoRespuesta.TryGetProperty(
                        "codigos_lista", out JsonElement lista)
                    && lista.ValueKind == JsonValueKind.Array)
                {
                    codigosProductosContexto = lista.EnumerateArray()
                        .Where(elemento =>
                            elemento.ValueKind == JsonValueKind.String)
                        .Select(elemento => elemento.GetString()!)
                        .ToList();
                }

                // Recuperar la página actual del inventario
                if (contextoRespuesta.TryGetProperty(
                        "pagina_actual", out JsonElement pagina)
                    && pagina.ValueKind == JsonValueKind.Number
                    && pagina.TryGetInt32(out int numeroPagina)
                    && numeroPagina >= 1)
                {
                    paginaActualContexto = numeroPagina;
                }

            }

            // Guardar la conversación únicamente cuando hubo éxito
            historialChat.Add(("user", pregunta));
            historialChat.Add(("model", respuestaIA));

            if (historialChat.Count > MAX_MENSAJES_HISTORIAL)
            {
                historialChat.RemoveRange(
                    0,
                    historialChat.Count - MAX_MENSAJES_HISTORIAL
                );
            }

            return respuestaIA;
        }


        // =====================================================
        // MOSTRAR ANIMACIÓN DE ESCRITURA
        // =====================================================

        private void MostrarEscribiendo()
        {
            if (burbujaEscribiendo != null)
                return;

            TextBlock texto = new TextBlock
            {
                Text = "Escribiendo.",
                FontSize = 14,
                Foreground = new SolidColorBrush(
                    Microsoft.UI.Colors.DarkGray)
            };

            burbujaEscribiendo = new Border
            {
                Background = new SolidColorBrush(
                    Windows.UI.Color.FromArgb(255, 229, 229, 229)),

                CornerRadius = new CornerRadius(12),
                Padding = new Thickness(14, 10, 14, 10),

                HorizontalAlignment = HorizontalAlignment.Left,
                Child = texto
            };

            PanelMensajes.Children.Add(burbujaEscribiendo);

            pasoAnimacion = 0;

            temporizadorEscritura = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(450)
            };

            temporizadorEscritura.Tick += (sender, e) =>
            {
                pasoAnimacion = (pasoAnimacion + 1) % 4;

                texto.Text = "Escribiendo" +
                             new string('.', pasoAnimacion);
            };

            temporizadorEscritura.Start();

            ScrollChatbot.UpdateLayout();

            ScrollChatbot.ChangeView(
                null,
                ScrollChatbot.ScrollableHeight,
                null);
        }


        // =====================================================
        // OCULTAR ANIMACIÓN DE ESCRITURA
        // =====================================================

        private void OcultarEscribiendo()
        {
            temporizadorEscritura?.Stop();
            temporizadorEscritura = null;

            if (burbujaEscribiendo != null)
            {
                PanelMensajes.Children.Remove(burbujaEscribiendo);
                burbujaEscribiendo = null;
            }
        }

        // =====================================================
        // INVENTARIO DISPONIBLE PARA GEMINI
        // =====================================================

        private string ObtenerInventarioParaIA()
        {
            var productos = _refacciones
                .Where(r => r.Activo)
                .OrderBy(r => r.Nombre)
                .Select(r => new
                {
                    codigo = r.Codigo,
                    nombre = r.Nombre,
                    marca = r.MarcaNombre,
                    categoria = r.CategoriaNombre,
                    precioMXN = r.Precio,
                    existencia = r.Stock,
                    universal = r.EsUniversal,
                    vehiculosCompatibles = r.EsUniversal
                        ? new[] { "Universal" }
                        : r.AutosDescripciones.ToArray()
                })
                .ToList();

            return JsonSerializer.Serialize(productos);
        }

        // =====================================================
        // ACTUALIZAR INVENTARIO PARA GEMINI
        // =====================================================

        private async Task<string> ObtenerInventarioActualizadoParaIAAsync()
        {
            // Recargar los datos desde los repositorios
            await repoRefacciones.ReloadAsync();
            await repoMarcas.ReloadAsync();
            await repoCategorias.ReloadAsync();
            await repoAutos.ReloadAsync();

            // Obtener una copia actualizada
            List<Refaccion> refaccionesActuales =
                (await repoRefacciones.GetAllAsync()).ToList();

            List<Marca> marcasActuales =
                (await repoMarcas.GetAllAsync()).ToList();

            List<Categoria> categoriasActuales =
                (await repoCategorias.GetAllAsync()).ToList();

            List<ModeloAuto> autosActuales =
                (await repoAutos.GetAllAsync()).ToList();

            // Preparar el inventario sin modificar
            // las colecciones utilizadas por Ventas
            var productos = refaccionesActuales
                .Where(r => r.Activo)
                .OrderBy(r => r.Nombre)
                .Select(r => new
                {
                    codigo = r.Codigo,
                    nombre = r.Nombre,

                    marca = marcasActuales
                        .FirstOrDefault(m => m.Id == r.MarcaId)?.Nombre
                        ?? "Sin marca",

                    categoria = categoriasActuales
                        .FirstOrDefault(c => c.Id == r.CategoriaId)?.Nombre
                        ?? "Sin categoría",

                    precioMXN = r.Precio,
                    existencia = r.Stock,
                    universal = r.EsUniversal,

                    vehiculosCompatibles = r.EsUniversal
                        ? new[] { "Universal" }
                        : (r.AutosCompatibles ?? new List<int>())
                            .Select(id => autosActuales
                                .FirstOrDefault(a => a.Id == id)?.DescripcionCompleta)
                            .Where(descripcion => descripcion != null)
                            .ToArray()
                })
                .ToList();

            return JsonSerializer.Serialize(productos);
        }

        // =====================================================
        // CATÁLOGO COMPLETO PARA EL ASISTENTE
        // =====================================================
        // Todo lo registrado en "Agregar elementos", tenga o no
        // productos. Se llama después de ObtenerInventarioActualizado...,
        // que ya recargó los repositorios.

        private async Task<object> ObtenerCatalogoParaIAAsync()
        {
            List<string> marcas =
                (await repoMarcas.GetAllAsync())
                .Select(m => m.Nombre)
                .Where(n => !string.IsNullOrWhiteSpace(n))
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToList();

            List<string> categorias =
                (await repoCategorias.GetAllAsync())
                .Select(c => c.Nombre)
                .Where(n => !string.IsNullOrWhiteSpace(n))
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .ToList();

            var autos =
                (await repoAutos.GetAllAsync())
                .Where(a => !string.IsNullOrWhiteSpace(a.Modelo))
                .Select(a => new
                {
                    marca = a.Marca,
                    modelo = a.Modelo,
                    anio_inicio = a.AnioInicio,
                    anio_fin = a.AnioFin
                })
                .ToList();

            return new
            {
                marcas,
                categorias,
                autos
            };
        }
    }
}
