using System;
using System.IO;

using Microsoft.Extensions.DependencyInjection;
using Microsoft.UI.Xaml;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;
using Refaccionaria.Frontend.ViewModels;

using QuestPDF.Infrastructure;

namespace Refaccionaria.Frontend;

public partial class App : Application
{
    public new static App Current => (App)Application.Current;

    public IServiceProvider Services { get; }

    public MainWindow? MainWindow { get; private set; }


    // =========================================================
    // CONSTRUCTOR
    // =========================================================

    public App()
    {
        this.InitializeComponent();

        QuestPDF.Settings.License = LicenseType.Community;

        UnhandledException += App_UnhandledException;

        Services = ConfigureServices();

    }


    // =========================================================
    // ERRORES NO CONTROLADOS
    // =========================================================

    private void App_UnhandledException(
        object sender,
        Microsoft.UI.Xaml.UnhandledExceptionEventArgs e)
    {
        System.Diagnostics.Debug.WriteLine(
            "ERROR NO CONTROLADO:"
        );

        System.Diagnostics.Debug.WriteLine(
            e.Exception.ToString()
        );
    }


    // =========================================================
    // SERVICIOS Y REPOSITORIOS
    // =========================================================

    private static IServiceProvider ConfigureServices()
    {
        var services = new ServiceCollection();


        // -----------------------------------------------------
        // PRODUCTOS
        // -----------------------------------------------------

        services.AddSingleton<IRepository<Refaccion>>(
            _ => new JsonRepository<Refaccion>(
                Ruta("refacciones.json")
            )
        );


        // -----------------------------------------------------
        // MARCAS
        // -----------------------------------------------------

        services.AddSingleton<IRepository<Marca>>(
            _ => new JsonRepository<Marca>(
                Ruta("marcas.json")
            )
        );


        // -----------------------------------------------------
        // CATEGORÍAS
        // -----------------------------------------------------

        services.AddSingleton<IRepository<Categoria>>(
            _ => new JsonRepository<Categoria>(
                Ruta("categorias.json")
            )
        );


        // -----------------------------------------------------
        // AUTOS
        // -----------------------------------------------------

        services.AddSingleton<IRepository<ModeloAuto>>(
            _ => new JsonRepository<ModeloAuto>(
                Ruta("autos.json")
            )
        );


        // -----------------------------------------------------
        // USUARIOS
        // -----------------------------------------------------

        services.AddSingleton<IRepository<Usuario>>(
            _ => new JsonRepository<Usuario>(
                Ruta("usuarios.json")
            )
        );


        // -----------------------------------------------------
        // VENTAS
        // -----------------------------------------------------

        services.AddSingleton<IRepository<Venta>>(
            _ => new JsonRepository<Venta>(
                Ruta("ventas.json")
            )
        );

        //------------------------------------------------------
        //   DETALLE VENTA
        //------------------------------------------------------

        services.AddSingleton<IRepository<DetalleVenta>>(
            _ => new JsonRepository<DetalleVenta>(
                Ruta("detalleVentas.json")
            )
        );

        // -----------------------------------------------------
        // VIEWMODELS
        // -----------------------------------------------------

        services.AddTransient<MainPageViewModel>();


        return services.BuildServiceProvider();
    }


    // =========================================================
    // RUTA DE LOS ARCHIVOS JSON
    // =========================================================

    private static string Ruta(string archivo)
    {
        string? carpetaData =
            BuscarCarpetaDataBackend();


        if (carpetaData == null)
        {
            throw new DirectoryNotFoundException(
                "No se encontró la carpeta " +
                "Refaccionaria.Backend\\Data."
            );
        }


        string rutaArchivo =
            Path.Combine(
                carpetaData,
                archivo
            );


        // Si por alguna razón el archivo todavía no existe,
        // se crea como un arreglo JSON vacío.
        if (!File.Exists(rutaArchivo))
        {
            File.WriteAllText(
                rutaArchivo,
                "[]"
            );
        }


        System.Diagnostics.Debug.WriteLine(
            $"JSON UTILIZADO: {rutaArchivo}"
        );


        return rutaArchivo;
    }


    // =========================================================
    // BUSCAR REFACCIONARIA.BACKEND\DATA
    // =========================================================

    private static string? BuscarCarpetaDataBackend()
    {
        DirectoryInfo? carpeta =
            new DirectoryInfo(
                AppContext.BaseDirectory
            );


        while (carpeta != null)
        {
            // -------------------------------------------------
            // CASO 1
            //
            // Estamos en alguna carpeta dentro de la solución
            // y encontramos:
            //
            // Refaccionaria.Backend\Data
            // -------------------------------------------------

            string posibleRuta =
                Path.Combine(
                    carpeta.FullName,
                    "Refaccionaria.Backend",
                    "Data"
                );


            if (Directory.Exists(posibleRuta))
            {
                return posibleRuta;
            }


            // -------------------------------------------------
            // CASO 2
            //
            // La carpeta actual ya es Refaccionaria.Backend
            // -------------------------------------------------

            if (string.Equals(
                    carpeta.Name,
                    "Refaccionaria.Backend",
                    StringComparison.OrdinalIgnoreCase))
            {
                string dataBackend =
                    Path.Combine(
                        carpeta.FullName,
                        "Data"
                    );


                if (Directory.Exists(dataBackend))
                {
                    return dataBackend;
                }
            }


            carpeta =
                carpeta.Parent;
        }


        return null;
    }


    // =========================================================
    // INICIO DE LA APLICACIÓN
    // =========================================================

    protected override void OnLaunched(
        LaunchActivatedEventArgs args)
    {
        try
        {
            MainWindow =
                new MainWindow();

            MainWindow.Activate();
        }
        catch (Exception ex)
        {
            System.Diagnostics.Debug.WriteLine(
                "ERROR AL INICIAR:"
            );

            System.Diagnostics.Debug.WriteLine(
                ex.ToString()
            );
        }
    }
}