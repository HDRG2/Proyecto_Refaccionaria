using QuestPDF.Fluent;
using QuestPDF.Helpers;
using QuestPDF.Infrastructure;

using Refaccionaria.Frontend.Models;

using System;
using System.Collections.Generic;
using System.Linq;

namespace Refaccionaria.Frontend.Services;

public static class ReporteVentasPdf
{
    // =========================================================
    // GENERAR PDF
    // =========================================================

    public static void Generar(
        string rutaArchivo,
        IEnumerable<Venta> ventas)
    {
        var listaVentas =
            ventas
                .OrderBy(v => v.Fecha)
                .ToList();

        decimal totalVendido =
            listaVentas.Sum(v => v.Total);

        int cantidadVentas =
            listaVentas.Count;

        int piezasVendidas =
            listaVentas
                .SelectMany(v => v.Lineas)
                .Sum(d => d.Cantidad);

        var productoMasVendido =
            listaVentas
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

        string productoTop =
            productoMasVendido == null
                ? "—"
                : $"{productoMasVendido.Nombre} ({productoMasVendido.Cantidad} piezas)";

        Document.Create(documento =>
        {
            documento.Page(pagina =>
            {
                pagina.Size(PageSizes.A4);

                pagina.Margin(35);

                pagina.DefaultTextStyle(
                    estilo => estilo.FontSize(10));

                // Encabezado
                pagina.Header().Element(
                    contenedor => CrearEncabezado(contenedor));

                // Contenido
                pagina.Content()
                    .PaddingVertical(20)
                    .Column(columna =>
                    {
                        columna.Spacing(15);

                        columna.Item().Element(
                            contenedor => CrearResumen(
                                contenedor,
                                totalVendido,
                                cantidadVentas,
                                piezasVendidas,
                                productoTop));

                        columna.Item().Element(
                            contenedor => CrearTablaVentas(
                                contenedor,
                                listaVentas));

                        columna.Item()
                            .PaddingTop(5)
                            .AlignRight()
                            .Text(
                                $"TOTAL GENERAL: {totalVendido:C}")
                            .FontSize(14)
                            .Bold()
                            .FontColor("#C51F1F");
                    });

                // Pie de página
                pagina.Footer().Element(
                    contenedor => CrearPiePagina(contenedor));
            });
        })
        .GeneratePdf(rutaArchivo);
    }


    // =========================================================
    // ENCABEZADO
    // =========================================================

    private static void CrearEncabezado(
        IContainer contenedor)
    {
        contenedor.Column(columna =>
        {
            columna.Item()
                .AlignCenter()
                .Text("EL PISTÓN")
                .FontSize(25)
                .Bold()
                .FontColor("#C51F1F");

            columna.Item()
                .AlignCenter()
                .Text("REFACCIONARIA")
                .FontSize(11)
                .Bold();

            columna.Item()
                .PaddingTop(4)
                .AlignCenter()
                .Text("REPORTE DE VENTAS")
                .FontSize(16)
                .Bold();

            columna.Item()
                .PaddingTop(4)
                .AlignCenter()
                .Text(
                    $"Generado: {DateTime.Now:dd/MM/yyyy HH:mm}");

            columna.Item()
                .PaddingTop(12)
                .LineHorizontal(1)
                .LineColor("#FFC107");
        });
    }


    // =========================================================
    // RESUMEN GENERAL
    // =========================================================

    private static void CrearResumen(
        IContainer contenedor,
        decimal totalVendido,
        int cantidadVentas,
        int piezasVendidas,
        string productoTop)
    {
        contenedor.Column(columna =>
        {
            columna.Item()
                .Text("RESUMEN GENERAL")
                .FontSize(14)
                .Bold();

            columna.Item()
                .PaddingTop(8)
                .Table(tabla =>
                {
                    tabla.ColumnsDefinition(columnas =>
                    {
                        columnas.RelativeColumn();
                        columnas.RelativeColumn();
                        columnas.RelativeColumn();
                        columnas.RelativeColumn();
                    });

                    // -------------------------
                    // ENCABEZADOS
                    // -------------------------

                    CeldaEncabezado(tabla.Cell(), "TOTAL VENDIDO");
                    CeldaEncabezado(tabla.Cell(), "VENTAS");
                    CeldaEncabezado(tabla.Cell(), "PIEZAS");
                    CeldaEncabezado(tabla.Cell(), "MÁS VENDIDO");

                    // -------------------------
                    // VALORES
                    // -------------------------

                    CeldaValor(
                        tabla.Cell(),
                        totalVendido.ToString("C"));

                    CeldaValor(
                        tabla.Cell(),
                        cantidadVentas.ToString());

                    CeldaValor(
                        tabla.Cell(),
                        piezasVendidas.ToString());

                    CeldaValor(
                        tabla.Cell(),
                        productoTop);
                });
        });
    }


    // =========================================================
    // TABLA DE VENTAS
    // =========================================================

    private static void CrearTablaVentas(
        IContainer contenedor,
        List<Venta> ventas)
    {
        contenedor.Column(columna =>
        {
            columna.Item()
                .Text("VENTAS REGISTRADAS")
                .FontSize(14)
                .Bold();

            columna.Item()
                .PaddingTop(8)
                .Table(tabla =>
                {
                    tabla.ColumnsDefinition(columnas =>
                    {
                        columnas.RelativeColumn(2.3f);
                        columnas.RelativeColumn(1.8f);
                        columnas.RelativeColumn(1.4f);
                        columnas.RelativeColumn(1.3f);
                    });

                    // -------------------------
                    // ENCABEZADO
                    // -------------------------

                    tabla.Header(encabezado =>
                    {
                        CeldaEncabezado(
                            encabezado.Cell(),
                            "FOLIO");

                        CeldaEncabezado(
                            encabezado.Cell(),
                            "FECHA");

                        CeldaEncabezado(
                            encabezado.Cell(),
                            "MÉTODO");

                        CeldaEncabezado(
                            encabezado.Cell(),
                            "TOTAL",
                            true);
                    });

                    // -------------------------
                    // VENTAS
                    // -------------------------

                    foreach (Venta venta in ventas)

                    {
                        CeldaTabla(
                            tabla.Cell(),
                            venta.Folio);

                        CeldaTabla(
                            tabla.Cell(),
                            venta.Fecha.ToString(
                                "dd/MM/yyyy HH:mm"));

                        CeldaTabla(
                            tabla.Cell(),
                            venta.MetodoPago);

                        CeldaTabla(
                            tabla.Cell(),
                            venta.Total.ToString("C"),
                            true);
                    }
                });
        });
    }


    // =========================================================
    // CELDA DE ENCABEZADO
    // =========================================================

    private static void CeldaEncabezado(
        IContainer celda,
        string texto,
        bool alinearDerecha = false)
    {
        var contenido =
            celda
                .Background("#222222")
                .Padding(7);

        if (alinearDerecha)
            contenido = contenido.AlignRight();

        contenido
            .Text(texto)
            .FontColor("#FFC107")
            .Bold();
    }


    // =========================================================
    // VALOR DEL RESUMEN
    // =========================================================

    private static void CeldaValor(
        IContainer celda,
        string texto)
    {
        celda
            .BorderBottom(1)
            .BorderColor("#DDDDDD")
            .Padding(7)
            .Text(texto);
    }


    // =========================================================
    // CELDA DE TABLA
    // =========================================================

    private static void CeldaTabla(
        IContainer celda,
        string texto,
        bool alinearDerecha = false)
    {
        var contenido =
            celda
                .BorderBottom(1)
                .BorderColor("#E0E0E0")
                .Padding(7);

        if (alinearDerecha)
            contenido = contenido.AlignRight();

        contenido.Text(texto);
    }


    // =========================================================
    // PIE DE PÁGINA
    // =========================================================

    private static void CrearPiePagina(
        IContainer contenedor)
    {
        contenedor
            .AlignCenter()
            .Text(texto =>
            {
                texto.Span(
                    "EL PISTÓN · Reporte de ventas · Página ");

                texto.CurrentPageNumber();

                texto.Span(" de ");

                texto.TotalPages();
            });
    }
}