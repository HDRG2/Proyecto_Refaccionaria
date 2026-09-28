using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;

using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using System.Collections.Generic;

using Refaccionaria.Frontend.Models;
using Refaccionaria.Frontend.Services;

namespace Refaccionaria.Frontend.Views;

public sealed partial class PanelAdmin : Page
{
    private List<Venta> ventasReporteActual = new();

    private bool filtrosReporteListos = false;
    // =========================================================
    // ACTUALIZAR RESUMEN DE REPORTES
    // =========================================================

    private void ActualizarResumenVentas()
    {
        // Si todavía no se ha preparado el filtro,
        // mostramos HOY por defecto.
        if (!filtrosReporteListos)
        {
            filtrosReporteListos = true;

            if (CmbPeriodoReporte != null)
            {
                CmbPeriodoReporte.SelectedIndex = 0;
            }
        }

        AplicarFiltroReporte();
    }


    // =========================================================
    // FILTRAR REPORTE POR PERÍODO
    // =========================================================

    private void AplicarFiltroReporte()
    {
        if (ventas == null)
            return;

        DateTime hoy = DateTime.Today;

        DateTime? desde = null;
        DateTime? hasta = null;

        int periodo =
            CmbPeriodoReporte?.SelectedIndex ?? 0;


        switch (periodo)
        {
            // HOY
            case 0:

                desde = hoy;
                hasta = hoy;

                TxtPeriodoReporte.Text =
                    $"Hoy - {hoy:dd/MM/yyyy}";

                break;


            // AYER
            case 1:

                desde = hoy.AddDays(-1);
                hasta = hoy.AddDays(-1);

                TxtPeriodoReporte.Text =
                    $"Ayer - {hoy.AddDays(-1):dd/MM/yyyy}";

                break;


            // ÚLTIMOS 7 DÍAS
            case 2:

                desde = hoy.AddDays(-6);
                hasta = hoy;

                TxtPeriodoReporte.Text =
                    "Últimos 7 días";

                break;


            // ÚLTIMAS 2 SEMANAS
            case 3:

                desde = hoy.AddDays(-13);
                hasta = hoy;

                TxtPeriodoReporte.Text =
                    "Últimas 2 semanas";

                break;


            // ÚLTIMAS 3 SEMANAS
            case 4:

                desde = hoy.AddDays(-20);
                hasta = hoy;

                TxtPeriodoReporte.Text =
                    "Últimas 3 semanas";

                break;


            // ESTE MES
            case 5:

                desde =
                    new DateTime(
                        hoy.Year,
                        hoy.Month,
                        1
                    );

                hasta = hoy;

                TxtPeriodoReporte.Text =
                    $"{hoy:MMMM yyyy}";

                break;


            // TODO EL HISTORIAL
            case 6:

                TxtPeriodoReporte.Text =
                    "Todo el historial";

                break;


            // PERSONALIZADO
            case 7:

                if (FechaReporteDesde.Date.HasValue)
                {
                    desde =
                        FechaReporteDesde.Date.Value.Date;
                }

                if (FechaReporteHasta.Date.HasValue)
                {
                    hasta =
                        FechaReporteHasta.Date.Value.Date;
                }

                if (desde.HasValue &&
                    hasta.HasValue)
                {
                    TxtPeriodoReporte.Text =
                        $"{desde.Value:dd/MM/yyyy} - " +
                        $"{hasta.Value:dd/MM/yyyy}";
                }
                else
                {
                    TxtPeriodoReporte.Text =
                        "Selecciona las fechas";
                }

                break;
        }


        IEnumerable<Venta> consulta =
            ventas;


        if (desde.HasValue)
        {
            consulta =
                consulta.Where(
                    v => v.Fecha.Date >= desde.Value.Date
                );
        }


        if (hasta.HasValue)
        {
            consulta =
                consulta.Where(
                    v => v.Fecha.Date <= hasta.Value.Date
                );
        }


        ventasReporteActual =
            consulta
                .OrderByDescending(v => v.Fecha)
                .ToList();


        // Actualizar tabla
        TablaVentas.ItemsSource =
            ventasReporteActual;


        // Actualizar tarjetas
        ActualizarTarjetasReporte(
            ventasReporteActual
        );
    }


    // =========================================================
    // ACTUALIZAR TARJETAS DEL REPORTE
    // =========================================================

    private void ActualizarTarjetasReporte(
        List<Venta> ventasFiltradas)
    {
        decimal totalVendido =
            ventasFiltradas.Sum(v => v.Total);


        int cantidadVentas =
            ventasFiltradas.Count;


        int piezasVendidas =
            ventasFiltradas
                .SelectMany(v => v.Lineas)
                .Sum(d => d.Cantidad);


        var productoMasVendido =
            ventasFiltradas
                .SelectMany(v => v.Lineas)
                .Where(d => d.Refaccion != null)
                .GroupBy(
                    d => d.Refaccion!.Nombre
                )
                .Select(g => new
                {
                    Nombre = g.Key,

                    Cantidad =
                        g.Sum(d => d.Cantidad)
                })
                .OrderByDescending(
                    x => x.Cantidad
                )
                .FirstOrDefault();


        TxtRepTotal.Text =
            totalVendido.ToString("C");


        TxtRepVentas.Text =
            cantidadVentas.ToString();


        TxtRepPiezas.Text =
            piezasVendidas.ToString();


        TxtRepTop.Text =
            productoMasVendido?.Nombre
            ?? "—";


        TxtRepTopDetalle.Text =
            productoMasVendido != null
                ? $"{productoMasVendido.Cantidad} piezas"
                : string.Empty;


        // Este texto ahora indica cuántas ventas
        // existen en el período seleccionado.
        TxtRepHoy.Text =
            cantidadVentas == 1
                ? "1 venta en este período"
                : $"{cantidadVentas} ventas en este período";
    }


    // =========================================================
    // CAMBIAR PERÍODO
    // =========================================================

    private void PeriodoReporte_SelectionChanged(
        object sender,
        SelectionChangedEventArgs e)
    {
        if (FechaReporteDesde == null ||
            FechaReporteHasta == null)
        {
            return;
        }


        bool personalizado =
            CmbPeriodoReporte.SelectedIndex == 7;


        FechaReporteDesde.IsEnabled =
            personalizado;

        FechaReporteHasta.IsEnabled =
            personalizado;


        // Al entrar por primera vez a personalizado,
        // colocamos HOY en ambos calendarios.
        if (personalizado)
        {
            if (!FechaReporteDesde.Date.HasValue)
            {
                FechaReporteDesde.Date =
                    DateTimeOffset.Now;
            }


            if (!FechaReporteHasta.Date.HasValue)
            {
                FechaReporteHasta.Date =
                    DateTimeOffset.Now;
            }
        }


        AplicarFiltroReporte();
    }


    // =========================================================
    // CAMBIAR FECHAS PERSONALIZADAS
    // =========================================================

    private void FechaReporte_DateChanged(
        CalendarDatePicker sender,
        CalendarDatePickerDateChangedEventArgs args)
    {
        if (CmbPeriodoReporte == null)
            return;


        if (CmbPeriodoReporte.SelectedIndex != 7)
            return;


        if (!FechaReporteDesde.Date.HasValue ||
            !FechaReporteHasta.Date.HasValue)
        {
            return;
        }


        DateTime desde =
            FechaReporteDesde.Date.Value.Date;


        DateTime hasta =
            FechaReporteHasta.Date.Value.Date;


        if (desde > hasta)
        {
            TxtPeriodoReporte.Text =
                "La fecha inicial es posterior a la final";

            TablaVentas.ItemsSource =
                new List<Venta>();

            ActualizarTarjetasReporte(
                new List<Venta>()
            );

            return;
        }


        AplicarFiltroReporte();
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
            if (ventasReporteActual.Count == 0)
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
                ventasReporteActual);

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
