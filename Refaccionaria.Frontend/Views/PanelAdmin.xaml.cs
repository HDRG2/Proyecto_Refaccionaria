using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;

using Microsoft.Extensions.DependencyInjection;

using System;
using System.IO;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;
using Refaccionaria.Frontend.Services;

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

    private readonly ProductoService productoService;

    private readonly UsuarioService usuarioService;

    // =========================================================
    // CONSTRUCTOR
    // =========================================================

    public PanelAdmin(string usuario)
    {
        InitializeComponent();

        productoService = new ProductoService(
            repoRefacciones 
        );

        usuarioService = new UsuarioService(
            repoUsuarios
        );

        usuarioActual = usuario;

        TxtUsuarioActual.Text = usuario;
    }

    // =========================================================
    // CARGAR PANEL
    // =========================================================

    private async void Page_Loaded(object sender, RoutedEventArgs e)
    {
        try
        {
            await CargarDatosAsync();

            ventanaLista = true;

            MostrarInventario();
        }
        catch (ErrorArchivoDatosException ex)
        {
            bool restaurado =
                await RestaurarArchivoAsync(
                    ex.NombreArchivo,
                    ex.Message
                );

            if (!restaurado)
            {
                Application.Current.Exit(); // para cuando el usuario seleccione que no quiere restaurar, se cierre el programa
                return;
            }

            try
            {
                await CargarDatosAsync();

                ventanaLista = true;

                MostrarInventario();
            }
            catch (Exception segundoError)
            {
                await MostrarMensaje(
                    "No se pudieron cargar los datos",
                    segundoError.Message
                );
            }
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
    // CARGAR DATOS DE LOS JSON
    // =========================================================

    private async Task CargarDatosAsync()
    {
        // =========================================================
        // REFACCIONES
        // =========================================================

        IEnumerable<Refaccion> listaRefacciones =
            await CargarArchivoAsync(
                repoRefacciones,
                "refacciones.json"
            );

        todasLasRefacciones =
            new ObservableCollection<Refaccion>(
                listaRefacciones
            );

        refacciones =
            new ObservableCollection<Refaccion>(
                todasLasRefacciones.Where(r => r.Activo)
            );

        refaccionesInactivas =
            new ObservableCollection<Refaccion>(
                todasLasRefacciones.Where(r => !r.Activo)
            );


        // =========================================================
        // MARCAS
        // =========================================================

        IEnumerable<Marca> listaMarcas =
            await CargarArchivoAsync(
                repoMarcas,
                "marcas.json"
            );

        marcas =
            new ObservableCollection<Marca>(
                listaMarcas
            );


        // =========================================================
        // CATEGORÍAS
        // =========================================================

        IEnumerable<Categoria> listaCategorias =
            await CargarArchivoAsync(
                repoCategorias,
                "categorias.json"
            );

        categorias =
            new ObservableCollection<Categoria>(
                listaCategorias
            );


        // =========================================================
        // AUTOS
        // =========================================================

        IEnumerable<ModeloAuto> listaAutos =
            await CargarArchivoAsync(
                repoAutos,
                "autos.json"
            );

        autos =
            new ObservableCollection<ModeloAuto>(
                listaAutos
            );
        
        // =========================================================
        // VALIDAR RELACIONES ENTRE LOS ARCHIVOS JSON
        // =========================================================
        try
        {
            ValidarRelacionesDatos();
        }
        catch (InvalidDataException ex)
        {
            throw new ErrorArchivoDatosException(
                "refacciones.json",
                ex
            );
        }

        // =========================================================
        // USUARIOS
        // =========================================================

        IEnumerable<Usuario> listaUsuarios =
            await CargarArchivoAsync(
                repoUsuarios,
                "usuarios.json"
            );

        vendedores =
            new ObservableCollection<Usuario>(
                listaUsuarios.Where(u => u.Rol == "Vendedor")
            );


        // =========================================================
        // VENTAS
        // =========================================================

        IEnumerable<Venta> listaVentas =
            await CargarArchivoAsync(
                repoVentas,
                "ventas.json"
            );


        // =========================================================
        // DETALLES DE VENTA
        // =========================================================

        IEnumerable<DetalleVenta> listaDetalles =
            await CargarArchivoAsync(
                repoDetalleVentas,
                "detalleVentas.json"
            );

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


        // =========================================================
        // COMPLETAR DATOS
        // =========================================================

        foreach (Refaccion refaccion in todasLasRefacciones)
        {
            CompletarDatosRefaccion(refaccion);
        }


        // =========================================================
        // CONECTAR CON XAML
        // =========================================================

        ListaTarjetas.ItemsSource = refacciones;
        ListaEditarProductos.ItemsSource = refacciones;
        ListaProductosRetirados.ItemsSource = refaccionesInactivas;

        TablaEmpleados.ItemsSource = vendedores;
        TablaVentas.ItemsSource = ventas;

        CmbMarca.ItemsSource = marcas;
        CmbMarca.DisplayMemberPath = "Nombre";

        CmbFormMarca.ItemsSource = marcas;
        CmbFormMarca.DisplayMemberPath = "Nombre";

        CmbFormCategoria.ItemsSource = categorias;
        CmbFormCategoria.DisplayMemberPath = "Nombre";

        LstFormAutos.ItemsSource = autos;

        ActualizarTodo();
        ActualizarResumenVentas();
        ActualizarResumenEmpleados();
    }

    // =========================================================
    // VALIDAR RELACIONES ENTRE LOS ARCHIVOS JSON
    // =========================================================

    private void ValidarRelacionesDatos()
    {
        // -----------------------------------------------------
        // IDs existentes
        // -----------------------------------------------------

        HashSet<int> idsMarcas =
            marcas
            .Select(m => m.Id)
            .ToHashSet();

        HashSet<int> idsCategorias =
            categorias
            .Select(c => c.Id)
            .ToHashSet();

        HashSet<int> idsAutos =
            autos
            .Select(a => a.Id)
            .ToHashSet();


        // -----------------------------------------------------
        // VALIDAR CADA REFACCIÓN
        // -----------------------------------------------------

        foreach (Refaccion refaccion in todasLasRefacciones)
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
                            $"({refaccion.Codigo}) contiene el AutoId " +
                            $"{autoId}, pero ese vehículo " +
                            $"no existe en autos.json."
                        );
                    }
                }
            }
        }
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

    // =========================================================
    // ERROR DE ARCHIVO DE DATOS
    // =========================================================

    private sealed class ErrorArchivoDatosException : Exception
    {
        public string NombreArchivo { get; }

        public ErrorArchivoDatosException(
            string nombreArchivo,
            Exception innerException)
            : base(innerException.Message, innerException)
        {
            NombreArchivo = nombreArchivo;
        }
    }

    // =========================================================
    // CARGAR ARCHIVO JSON
    // =========================================================

    private async Task<IEnumerable<T>> CargarArchivoAsync<T>(
        IRepository<T> repositorio,
        string nombreArchivo)
        where T : class, IEntity
    {
        try
        {
            await repositorio.ReloadAsync();

            return await repositorio.GetAllAsync();
        }
        catch (Exception ex)
        {
            throw new ErrorArchivoDatosException(
                nombreArchivo,
                ex
            );
        }
    }

    // =========================================================
    // PREGUNTAR SI SE DESEA RESTAURAR
    // =========================================================

    private async Task<bool> PreguntarRestauracionAsync(
     string nombreArchivo,
     string detalleError)
    {
        // Esperar a que la página tenga un XamlRoot válido
        while (XamlRoot == null)
        {
            await Task.Delay(50);
        }

        ContentDialog dialogo = new()
        {
            Title = "Problema en los datos",

            Content =
                $"Se detectó un problema en '{nombreArchivo}'.\n\n" +
                $"{detalleError}\n\n" +
                "Existe una copia estable de este archivo.\n\n" +
                "¿Deseas restaurarla?",

            PrimaryButtonText = "Restaurar copia estable",
            CloseButtonText = "Cancelar",

            DefaultButton = ContentDialogButton.Close,

            XamlRoot = XamlRoot
        };

        ContentDialogResult resultado =
            await dialogo.ShowAsync();

        return resultado ==
               ContentDialogResult.Primary;
    }


    // =========================================================
    // RESTAURAR ARCHIVO
    // =========================================================

    private async Task<bool> RestaurarArchivoAsync(
        string nombreArchivo,
        string detalleError)
    {
        bool restaurar =
            await PreguntarRestauracionAsync(
                nombreArchivo,
                detalleError
            );

        if (!restaurar)
        {
            return false;
        }

        try
        {
            App.RestaurarArchivoBaseEstable(
                nombreArchivo
            );

            await MostrarMensaje(
                "Archivo restaurado",
                $"'{nombreArchivo}' fue restaurado correctamente " +
                "desde la BaseEstable.\n\n" +
                "La versión anterior también fue guardada en " +
                "Backups/AntesDeRestaurar."
            );

            return true;
        }
        catch (Exception ex)
        {
            await MostrarMensaje(
                "No se pudo restaurar",
                ex.Message
            );

            return false;
        }
    }

}


