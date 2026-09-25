using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;

using Microsoft.Extensions.DependencyInjection;

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;

namespace Refaccionaria.Frontend.Views;

public sealed partial class PanelAdmin : Page
{
    // =========================================================
    // COLECCIONES
    // =========================================================

    private ObservableCollection<Refaccion> todasLasRefacciones = new();
    private ObservableCollection<Refaccion> refacciones = new();

    private ObservableCollection<Refaccion> refaccionesInactivas = new();

    private ObservableCollection<Usuario> vendedores = new();

    private ObservableCollection<Venta> ventas = new();

    private ObservableCollection<Marca> marcas = new();

    private ObservableCollection<Categoria> categorias = new();

    private ObservableCollection<ModeloAuto> autos = new();
    // =========================================================
    // ESTADO DEL PANEL
    // =========================================================

    private bool ventanaLista = false;

    private readonly string usuarioActual;

    private string modoFormulario = string.Empty;

    private Refaccion? refaccionEditando = null;
    private Usuario? usuarioEditando = null;


    // =========================================================
    // REPOSITORIOS JSON
    // =========================================================

    private readonly IRepository<Refaccion> repoRefacciones =
        App.Current.Services.GetRequiredService<IRepository<Refaccion>>();

    private readonly IRepository<Usuario> repoUsuarios =
        App.Current.Services.GetRequiredService<IRepository<Usuario>>();

    private readonly IRepository<Venta> repoVentas =
        App.Current.Services.GetRequiredService<IRepository<Venta>>();

    private readonly IRepository<Marca> repoMarcas =
        App.Current.Services.GetRequiredService<IRepository<Marca>>();

    private readonly IRepository<Categoria> repoCategorias =
        App.Current.Services.GetRequiredService<IRepository<Categoria>>();

    private readonly IRepository<ModeloAuto> repoAutos =
        App.Current.Services.GetRequiredService<IRepository<ModeloAuto>>();

    private readonly IRepository<DetalleVenta> repoDetalleVentas =
    App.Current.Services.GetRequiredService<IRepository<DetalleVenta>>();


    // =========================================================
    // CONSTRUCTOR
    // =========================================================

    public PanelAdmin(string usuario)
    {
        InitializeComponent();

        usuarioActual = usuario;

        TxtUsuarioActual.Text = usuario;
    }


    // =========================================================
    // CARGAR PANEL
    // =========================================================

    private async void Page_Loaded(object sender, RoutedEventArgs e)
    {
        await CargarDatosAsync();

        ventanaLista = true;

        MostrarInventario();
    }


    // =========================================================
    // CARGAR DATOS DE LOS JSON
    // =========================================================

    private async Task CargarDatosAsync()
    {
        // -----------------------------------------------------
        // REFACCIONES
        // -----------------------------------------------------

        todasLasRefacciones = new ObservableCollection<Refaccion>(
            await repoRefacciones.GetAllAsync()
        );

        refacciones = new ObservableCollection<Refaccion>(
            todasLasRefacciones.Where(r => r.Activo)
        );

        refaccionesInactivas = new ObservableCollection<Refaccion>(
            todasLasRefacciones.Where(r => !r.Activo)
        );

        // -----------------------------------------------------
        // MARCAS
        // -----------------------------------------------------

        marcas = new ObservableCollection<Marca>(
            await repoMarcas.GetAllAsync()
        );


        // -----------------------------------------------------
        // CATEGORÍAS
        // -----------------------------------------------------

        categorias = new ObservableCollection<Categoria>(
            await repoCategorias.GetAllAsync()
        );


        // -----------------------------------------------------
        // AUTOS
        // -----------------------------------------------------

        autos = new ObservableCollection<ModeloAuto>(
            await repoAutos.GetAllAsync()
        );


        // -----------------------------------------------------
        // USUARIOS / VENDEDORES
        // -----------------------------------------------------

        vendedores = new ObservableCollection<Usuario>(
            (await repoUsuarios.GetAllAsync())
                .Where(u => u.Rol == "Vendedor")
        );


        // -----------------------------------------------------
        // VENTAS Y DETALLES DE CADA VENTA
        // -----------------------------------------------------

        var listaVentas = await repoVentas.GetAllAsync();
        var listaDetalles = await repoDetalleVentas.GetAllAsync();

        ventas = new ObservableCollection<Venta>();

        foreach (Venta venta in listaVentas)
        {
            venta.Lineas.Clear();

            foreach (DetalleVenta detalle in
                     listaDetalles.Where(d => d.VentaId == venta.Id))
            {
                venta.Lineas.Add(detalle);
            }

            ventas.Add(venta);
        }


        // -----------------------------------------------------
        // COMPLETAR DATOS DE REFACCIONES
        // -----------------------------------------------------

        foreach (Refaccion refaccion in todasLasRefacciones)
        {
            CompletarDatosRefaccion(refaccion);
        }


        // -----------------------------------------------------
        // CONECTAR CON EL XAML
        // -----------------------------------------------------

        ListaTarjetas.ItemsSource = refacciones;

        ListaEditarProductos.ItemsSource = refacciones;

        ListaProductosRetirados.ItemsSource = refaccionesInactivas;

        TablaEmpleados.ItemsSource = vendedores;

        TablaVentas.ItemsSource = ventas;


        // -----------------------------------------------------
        // COMBOBOX DE MARCAS
        // -----------------------------------------------------

        CmbMarca.ItemsSource = marcas;
        CmbMarca.DisplayMemberPath = "Nombre";


        // -----------------------------------------------------
        // COMBOBOX DEL FORMULARIO
        // -----------------------------------------------------

        CmbFormMarca.ItemsSource = marcas;
        CmbFormMarca.DisplayMemberPath = "Nombre";

        CmbFormCategoria.ItemsSource = categorias;
        CmbFormCategoria.DisplayMemberPath = "Nombre";


        // -----------------------------------------------------
        // AUTOS DEL FORMULARIO
        // -----------------------------------------------------

        LstFormAutos.ItemsSource = autos;
        


        // -----------------------------------------------------
        // ACTUALIZAR CONTADORES
        // -----------------------------------------------------

        ActualizarTodo();
        ActualizarResumenVentas();
        ActualizarResumenEmpleados();
    }


    // =========================================================
    // COMPLETAR INFORMACIÓN DE UNA REFACCIÓN
    // =========================================================

    private void CompletarDatosRefaccion(Refaccion refaccion)
    {
        // -----------------------------------------------------
        // MARCA
        // -----------------------------------------------------

        Marca? marca = marcas.FirstOrDefault(
            m => m.Id == refaccion.MarcaId
        );

        refaccion.MarcaNombre =
            marca?.Nombre ?? "Sin marca";


        // -----------------------------------------------------
        // CATEGORÍA
        // -----------------------------------------------------

        Categoria? categoria = categorias.FirstOrDefault(
            c => c.Id == refaccion.CategoriaId
        );

        refaccion.CategoriaNombre =
            categoria?.Nombre ?? "Sin categoría";


        // -----------------------------------------------------
        // AUTOS COMPATIBLES
        // -----------------------------------------------------

        refaccion.AutosDescripciones.Clear();

        if (refaccion.AutosCompatibles != null)
        {
            foreach (int autoId in refaccion.AutosCompatibles)
            {
                ModeloAuto? auto = autos.FirstOrDefault(
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
    }


    // =========================================================
    // ACTUALIZAR RESUMEN DEL INVENTARIO
    // =========================================================

    private void ActualizarTodo()
    {
        int totalProductos = refacciones.Count;
        int totalUnidades = refacciones.Sum(r => r.Stock);
        int totalStockBajo = refacciones.Count(r => r.StockBajo);
        int totalMarcas = refacciones.Select(r => r.MarcaId).Distinct().Count();
        decimal valorInventario = refacciones.Sum(r => r.Precio * r.Stock);

        TxtResumenPiezas.Text = totalProductos.ToString();
        TxtResumenUnidades.Text = totalUnidades.ToString();
        TxtResumenMarcas.Text = totalMarcas.ToString();
        TxtResumenResurtir.Text = totalStockBajo.ToString();
        TxtResumenValor.Text = valorInventario.ToString("C");

        TxtCardProductos.Text = totalProductos.ToString();
        TxtCardUnidades.Text = totalUnidades.ToString();
        TxtCardStockBajo.Text = totalStockBajo.ToString();
        TxtCardValor.Text = valorInventario.ToString("C");

        TxtResultado.Text =
            totalProductos == 1
                ? "1 producto disponible"
                : $"{totalProductos} productos disponibles";

        ActualizarProductosRetirados();

        ActualizarListaEditar();
    }


    private void ActualizarListaEditar()
    {
        string texto =
            TxtBuscarEditar.Text.Trim();

        IEnumerable<Refaccion> resultado =
            refacciones;

        if (!string.IsNullOrWhiteSpace(texto))
        {
            resultado =
                refacciones.Where(
                    r =>
                        r.Nombre.Contains(
                            texto,
                            StringComparison.OrdinalIgnoreCase
                        ) ||
                        r.Codigo.Contains(
                            texto,
                            StringComparison.OrdinalIgnoreCase
                        ) ||
                        r.MarcaNombre.Contains(
                            texto,
                            StringComparison.OrdinalIgnoreCase
                        ) ||
                        r.CategoriaNombre.Contains(
                            texto,
                            StringComparison.OrdinalIgnoreCase
                        )
                );
        }

        ListaEditarProductos.ItemsSource =
            resultado.ToList();

        ActualizarEstadoListaEditar();
    }


    private void ActualizarProductosRetirados()
    {
        ListaProductosRetirados.ItemsSource = refaccionesInactivas;

        int cantidad = refaccionesInactivas.Count;

        TxtResumenRetirados.Text =
            cantidad == 1
                ? "1 producto retirado del inventario."
                : $"{cantidad} productos retirados del inventario.";

        ListaProductosRetirados.Visibility =
            cantidad > 0 ? Visibility.Visible : Visibility.Collapsed;

        PanelSinRetirados.Visibility =
            cantidad == 0 ? Visibility.Visible : Visibility.Collapsed;
    }


    // =========================================================
    // MOSTRAR INVENTARIO
    // =========================================================

    private void MostrarInventario()
    {
        VistaInventario.Visibility = Visibility.Visible;

        VistaEditarProducto.Visibility = Visibility.Collapsed;

        VistaProductosRetirados.Visibility = Visibility.Collapsed;

        VistaEmpleados.Visibility = Visibility.Collapsed;

        VistaReportes.Visibility = Visibility.Collapsed;

        Formulario.Visibility = Visibility.Collapsed;
    }


    // =========================================================
    // MOSTRAR EDITAR PRODUCTO
    // =========================================================

    private void MostrarEditarProducto()
    {
        VistaInventario.Visibility = Visibility.Collapsed;

        VistaEditarProducto.Visibility = Visibility.Visible;

        VistaProductosRetirados.Visibility = Visibility.Collapsed;

        VistaEmpleados.Visibility = Visibility.Collapsed;

        VistaReportes.Visibility = Visibility.Collapsed;

        Formulario.Visibility = Visibility.Collapsed;

        TxtBuscarEditar.Text = string.Empty;

        ListaEditarProductos.ItemsSource = refacciones;

        ActualizarEstadoListaEditar();
    }


    // =========================================================
    // MOSTRAR PRODUCTOS RETIRADOS
    // =========================================================

    private void MostrarProductosRetirados()
    {
        VistaInventario.Visibility = Visibility.Collapsed;
        VistaEditarProducto.Visibility = Visibility.Collapsed;
        VistaProductosRetirados.Visibility = Visibility.Visible;
        VistaEmpleados.Visibility = Visibility.Collapsed;
        VistaReportes.Visibility = Visibility.Collapsed;
        Formulario.Visibility = Visibility.Collapsed;

        ActualizarProductosRetirados();
    }


    // =========================================================
    // MOSTRAR EMPLEADOS
    // =========================================================

    private void MostrarEmpleados()
    {
        VistaInventario.Visibility = Visibility.Collapsed;

        VistaEditarProducto.Visibility = Visibility.Collapsed;

        VistaProductosRetirados.Visibility = Visibility.Collapsed;

        VistaEmpleados.Visibility = Visibility.Visible;

        VistaReportes.Visibility = Visibility.Collapsed;

        Formulario.Visibility = Visibility.Collapsed;
    }


    // =========================================================
    // MOSTRAR REPORTES
    // =========================================================

    private void MostrarReportes()
    {
        VistaInventario.Visibility = Visibility.Collapsed;

        VistaEditarProducto.Visibility = Visibility.Collapsed;

        VistaProductosRetirados.Visibility = Visibility.Collapsed;

        VistaEmpleados.Visibility = Visibility.Collapsed;

        VistaReportes.Visibility = Visibility.Visible;

        Formulario.Visibility = Visibility.Collapsed;

        // Actualizar las estadísticas de ventas
        ActualizarResumenVentas();
    }


    // =========================================================
    // SALIR
    // =========================================================

    private async void Salir_Click(object sender, RoutedEventArgs e)
    {
        ContentDialog dialogo = new()
        {
            Title = "Cerrar sesión",
            Content = "¿Deseas cerrar la sesión?",
            PrimaryButtonText = "Cerrar sesión",
            CloseButtonText = "Cancelar",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = XamlRoot
        };

        ContentDialogResult resultado = await dialogo.ShowAsync();

        if (resultado != ContentDialogResult.Primary)
            return;

        // Regresar al login
        App.Current.MainWindow?.CerrarSesion();
    }


    // =========================================================
    // MENÚ LATERAL
    // =========================================================

    private void Menu_Checked(object sender, RoutedEventArgs e)
    {
        if (!ventanaLista)
            return;

        if (sender is not RadioButton opcion)
            return;

        // INVENTARIO
        if (ReferenceEquals(opcion, MenuInventario))
        {
            MostrarInventario();
            return;
        }

        // AGREGAR PRODUCTO
        if (ReferenceEquals(opcion, MenuAgregarProducto))
        {
            MostrarInventario();
            NuevoProducto_Click(sender, e);
            return;
        }

        // EDITAR PRODUCTO
        if (ReferenceEquals(opcion, MenuEditarProducto))
        {
            MostrarEditarProducto();
            return;
        }

        // PRODUCTOS RETIRADOS
        if (ReferenceEquals(opcion, MenuEliminarProducto))
        {
            MostrarProductosRetirados();
            return;
        }

        // EMPLEADOS
        if (ReferenceEquals(opcion, MenuEmpleados))
        {
            MostrarEmpleados();
            return;
        }

        // REPORTES DE VENTAS
        if (ReferenceEquals(opcion, MenuReportes))
        {
            MostrarReportes();
        }
    }

    // =========================================================
    // MOSTRAR MENSAJE
    // =========================================================

    private async Task MostrarMensaje(
        string titulo,
        string mensaje)
    {
        ContentDialog dialogo =
            new()
            {
                Title = titulo,

                Content = mensaje,

                CloseButtonText = "Aceptar",

                XamlRoot = XamlRoot
            };

        await dialogo.ShowAsync();
    }

    // =========================================================
    // TECLADO
    // =========================================================

    private void Ventana_KeyDown(
        object sender,
        KeyRoutedEventArgs e)
    {
        // ESC cierra el formulario
        if (e.Key ==
            Windows.System.VirtualKey.Escape)
        {
            if (Formulario.Visibility ==
                Visibility.Visible)
            {
                Formulario.Visibility =
                    Visibility.Collapsed;

                modoFormulario =
                    string.Empty;
            }
        }
    }


    // =========================================================
    // ACCESO INVENTARIO
    // =========================================================

    private void AccesoInventario_Click(
        object sender,
        RoutedEventArgs e)
    {
        MostrarInventario();

        MenuInventario.IsChecked =
            true;
    }


    // =========================================================
    // ACCESO AGREGAR PRODUCTO
    // =========================================================

    private void AccesoAgregarProducto_Click(
        object sender,
        RoutedEventArgs e)
    {
        MostrarInventario();

        MenuAgregarProducto.IsChecked =
            true;

        // Se llama directamente porque si el RadioButton
        // ya estaba seleccionado, Checked no vuelve a ejecutarse.
        NuevoProducto_Click(
            sender,
            e
        );
    }


    // =========================================================
    // ACCESO EMPLEADOS
    // =========================================================

    private void AccesoEmpleados_Click(
        object sender,
        RoutedEventArgs e)
    {
        MostrarEmpleados();

        MenuEmpleados.IsChecked =
            true;
    }


    // =========================================================
    // ACCESO VENTAS
    // =========================================================

    private void AccesoVentas_Click(
        object sender,
        RoutedEventArgs e)
    {
        MostrarReportes();

        MenuReportes.IsChecked =
            true;
    }

}


