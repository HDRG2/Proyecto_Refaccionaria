using Microsoft.Extensions.DependencyInjection;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media.Animation;

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;

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

        public VentaPage()
        {
            InitializeComponent();

            ListaRefacciones.ItemsSource =
                _resultados;

            ListaTicket.ItemsSource =
                _ticket;

            Loaded += VentaPage_Loaded;
        }


        // =========================================================
        // LOADED
        // =========================================================

        private async void VentaPage_Loaded(
            object sender,
            RoutedEventArgs e)
        {
            Loaded -= VentaPage_Loaded;

            await CargarDatosAsync();

            _listo = true;

            AplicarFiltros();

            ActualizarTotales();
        }


        // =========================================================
        // CARGAR DATOS
        // =========================================================

        private async Task CargarDatosAsync()
        {
            try
            {
                _refacciones =
                    (await repoRefacciones.GetAllAsync())
                    .ToList();

                _marcas =
                    (await repoMarcas.GetAllAsync())
                    .ToList();

                _categorias =
                    (await repoCategorias.GetAllAsync())
                    .ToList();

                _autos =
                    (await repoAutos.GetAllAsync())
                    .ToList();


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
            }
            catch (Exception ex)
            {
                await MostrarMensaje(
                    "Error al cargar datos",
                    ex.Message
                );
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
    }
}
