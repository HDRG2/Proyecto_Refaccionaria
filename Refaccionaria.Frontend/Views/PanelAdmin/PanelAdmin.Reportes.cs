using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;

using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Frontend.Models;
using Refaccionaria.Frontend.Services;

namespace Refaccionaria.Frontend.Views;

public sealed partial class PanelAdmin : Page
{
    // =========================================================
    // ACTUALIZAR RESUMEN DE REPORTES
    // =========================================================

    private void ActualizarResumenVentas()
    {
        var ventasRegistradas = ventas.ToList();

        decimal totalVendido =
            ventasRegistradas.Sum(v => v.Total);

        int cantidadVentas =
            ventasRegistradas.Count;

        int piezasVendidas =
            ventasRegistradas
                .SelectMany(v => v.Lineas)
                .Sum(d => d.Cantidad);

        var productoMasVendido =
            ventasRegistradas
                .SelectMany(v => v.Lineas)
                .Where(d => d.Refaccion != null)
                .GroupBy(d => d.Refaccion!.Nombre)
                .Select(g => new
                {
                    Nombre = g.Key,
                    Cantidad = g.Sum(d => d.Cantidad)
                })
                .OrderByDescending(x => x.Cantidad)
                .FirstOrDefault();

        TxtRepTotal.Text =
            totalVendido.ToString("C");

        TxtRepVentas.Text =
            cantidadVentas.ToString();

        TxtRepPiezas.Text =
            piezasVendidas.ToString();

        TxtRepTop.Text =
            productoMasVendido?.Nombre ?? "—";

        TxtRepTopDetalle.Text =
            productoMasVendido != null
                ? $"{productoMasVendido.Cantidad} piezas"
                : string.Empty;

        TxtRepHoy.Text =
            $"{ventasRegistradas.Count(v => v.Fecha.Date == DateTime.Today)} ventas hoy";
    }


    // =========================================================
    // VER TICKET
    // =========================================================

    private void VerTicketVenta_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (sender is not Button boton)
            return;

        if (boton.Tag is not Venta venta)
            return;

        MostrarTicketVenta(venta);
    }


    // =========================================================
    // MOSTRAR TICKET
    // =========================================================

    private void MostrarTicketVenta(Venta venta)
    {
        // -----------------------------------------------------
        // DATOS GENERALES
        // -----------------------------------------------------

        TxtTicketFolio.Text =
            venta.Folio;

        TxtTicketFecha.Text =
            venta.Fecha.ToString("dd/MM/yyyy HH:mm");

        TxtTicketMetodo.Text =
            venta.MetodoPago;


        // -----------------------------------------------------
        // REFERENCIA
        // -----------------------------------------------------

        bool tieneReferencia =
            !string.IsNullOrWhiteSpace(venta.Referencia);

        LblTicketReferencia.Visibility =
            tieneReferencia
                ? Visibility.Visible
                : Visibility.Collapsed;

        TxtTicketReferencia.Visibility =
            tieneReferencia
                ? Visibility.Visible
                : Visibility.Collapsed;

        TxtTicketReferencia.Text =
            venta.Referencia ?? string.Empty;


        // -----------------------------------------------------
        // PRODUCTOS
        // -----------------------------------------------------

        PanelTicketProductos.Children.Clear();

        decimal subtotal = 0m;

        foreach (DetalleVenta detalle in venta.Lineas)
        {
            decimal importe =
                detalle.Cantidad *
                detalle.PrecioUnitario;

            subtotal += importe;

            string nombre =
                detalle.Refaccion?.Nombre
                ?? $"Producto #{detalle.RefaccionId}";


            Grid fila = new Grid
            {
                MinHeight = 25,
                Padding = new Thickness(6, 3, 6, 3)
            };


            fila.ColumnDefinitions.Add(
                new ColumnDefinition
                {
                    Width = new GridLength(
                        1,
                        GridUnitType.Star)
                });

            fila.ColumnDefinitions.Add(
                new ColumnDefinition
                {
                    Width = new GridLength(55)
                });

            fila.ColumnDefinitions.Add(
                new ColumnDefinition
                {
                    Width = new GridLength(90)
                });

            fila.ColumnDefinitions.Add(
                new ColumnDefinition
                {
                    Width = new GridLength(95)
                });


            // PRODUCTO
            TextBlock txtNombre = new TextBlock
            {
                Text = nombre,
                FontSize = 10,
                Foreground = CrearColor(
                    34,
                    34,
                    34),

                TextWrapping =
                    TextWrapping.Wrap,

                VerticalAlignment =
                    VerticalAlignment.Center
            };

            Grid.SetColumn(
                txtNombre,
                0);


            // CANTIDAD
            TextBlock txtCantidad = new TextBlock
            {
                Text =
                    detalle.Cantidad.ToString(),

                FontSize = 10,

                Foreground = CrearColor(
                    34,
                    34,
                    34),

                HorizontalAlignment =
                    HorizontalAlignment.Center,

                VerticalAlignment =
                    VerticalAlignment.Center
            };

            Grid.SetColumn(
                txtCantidad,
                1);


            // PRECIO UNITARIO
            TextBlock txtPrecio = new TextBlock
            {
                Text =
                    detalle.PrecioUnitario
                        .ToString("C"),

                FontSize = 10,

                Foreground = CrearColor(
                    34,
                    34,
                    34),

                HorizontalAlignment =
                    HorizontalAlignment.Right,

                VerticalAlignment =
                    VerticalAlignment.Center
            };

            Grid.SetColumn(
                txtPrecio,
                2);


            // IMPORTE
            TextBlock txtImporte = new TextBlock
            {
                Text =
                    importe.ToString("C"),

                FontSize = 10,

                FontWeight =
                    Microsoft.UI.Text.FontWeights.SemiBold,

                Foreground = CrearColor(
                    34,
                    34,
                    34),

                HorizontalAlignment =
                    HorizontalAlignment.Right,

                VerticalAlignment =
                    VerticalAlignment.Center
            };

            Grid.SetColumn(
                txtImporte,
                3);


            fila.Children.Add(
                txtNombre);

            fila.Children.Add(
                txtCantidad);

            fila.Children.Add(
                txtPrecio);

            fila.Children.Add(
                txtImporte);


            PanelTicketProductos.Children.Add(
                fila);


            // Línea debajo del producto
            Border separador = new Border
            {
                Height = 1,

                Background =
                    CrearColor(
                        225,
                        225,
                        225)
            };

            PanelTicketProductos.Children.Add(
                separador);
        }


        // -----------------------------------------------------
        // TOTALES
        // -----------------------------------------------------

        decimal iva =
            venta.Total - subtotal;

        TxtTicketSubtotal.Text =
            subtotal.ToString("C");

        TxtTicketIva.Text =
            iva.ToString("C");

        TxtTicketTotal.Text =
            venta.Total.ToString("C");


        // -----------------------------------------------------
        // EFECTIVO
        // -----------------------------------------------------

        bool esEfectivo =
            venta.MetodoPago.Equals(
                "Efectivo",
                StringComparison.OrdinalIgnoreCase);


        PanelTicketEfectivo.Visibility =
            esEfectivo
                ? Visibility.Visible
                : Visibility.Collapsed;


        if (esEfectivo)
        {
            TxtTicketRecibido.Text =
                venta.Recibido.ToString("C");

            TxtTicketCambio.Text =
                venta.Cambio.ToString("C");
        }


        // -----------------------------------------------------
        // MOSTRAR PANEL
        // -----------------------------------------------------

        PanelTicketVenta.Visibility =
            Visibility.Visible;
    }


    // =========================================================
    // CERRAR TICKET
    // =========================================================

    private void CerrarTicket_Click(
        object sender,
        RoutedEventArgs e)
    {
        PanelTicketVenta.Visibility =
            Visibility.Collapsed;

        PanelTicketProductos.Children.Clear();
    }

    // =========================================================
    // DESCARGAR REPORTE DE VENTAS EN PDF
    // =========================================================

    private async void DescargarReporte_Click(
    object sender,
    RoutedEventArgs e)
    {
        try
        {
            if (ventas == null || ventas.Count == 0)
            {
                await MostrarMensajeReporte(
                    "No hay ventas registradas para generar el reporte.");

                return;
            }

            // =====================================================
            // BUSCAR LA CARPETA RAÍZ "Refaccionaria"
            // =====================================================

            string carpetaActual =
                AppContext.BaseDirectory;

            DirectoryInfo? directorio =
                new DirectoryInfo(carpetaActual);

            while (directorio != null &&
                   !Directory.Exists(
                       Path.Combine(
                           directorio.FullName,
                           "Refaccionaria.Frontend")))
            {
                directorio = directorio.Parent;
            }

            if (directorio == null)
            {
                await MostrarMensajeReporte(
                    "No se pudo localizar la carpeta principal de Refaccionaria.");

                return;
            }

            // =====================================================
            // CREAR CARPETA "Reportes"
            // =====================================================

            string carpetaReportes =
                Path.Combine(
                    directorio.FullName,
                    "Reportes");

            Directory.CreateDirectory(carpetaReportes);

            // =====================================================
            // CREAR NOMBRE DEL PDF
            // =====================================================

            string nombreArchivo =
                $"Reporte_Ventas_{DateTime.Now:yyyy-MM-dd_HHmmss}.pdf";

            string rutaCompleta =
                Path.Combine(
                    carpetaReportes,
                    nombreArchivo);

            // =====================================================
            // GENERAR PDF
            // =====================================================

            ReporteVentasPdf.Generar(
                rutaCompleta,
                ventas);

            // =====================================================
            // MENSAJE
            // =====================================================

            await MostrarMensajeReporte(
                $"El reporte se guardó correctamente.\n\n" +
                $"Carpeta: Reportes\n\n" +
                $"Archivo: {nombreArchivo}");
        }
        catch (Exception ex)
        {
            await MostrarMensajeReporte(
                $"No se pudo generar el reporte.\n\n{ex.Message}");
        }
    }


    // =========================================================
    // MENSAJE DEL REPORTE
    // =========================================================

    private async Task MostrarMensajeReporte(
        string mensaje)
    {
        ContentDialog dialogo = new ContentDialog
        {
            Title = "Reporte de ventas",
            Content = mensaje,
            CloseButtonText = "Aceptar",
            XamlRoot = this.XamlRoot
        };

        await dialogo.ShowAsync();
    }


    // =========================================================
    // COLOR AUXILIAR
    // =========================================================

    private SolidColorBrush CrearColor(
    byte rojo,
    byte verde,
    byte azul)
    {
        return new SolidColorBrush(
            Windows.UI.Color.FromArgb(
                255,
                rojo,
                verde,
                azul));
    }
}
