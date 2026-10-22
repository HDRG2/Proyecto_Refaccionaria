using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

using System;
using System.Globalization;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

using Refaccionaria.Frontend.Models;

namespace Refaccionaria.Frontend.Views;

// =============================================================
// AGREGAR ELEMENTOS
//
// Registra nuevos autos (autos.json), marcas de piezas
// (marcas.json) y categorías (categorias.json).
//
// Se agregan a las MISMAS colecciones (autos, marcas,
// categorias) que usa el formulario de producto, así que
// aparecen de inmediato en "Agregar producto" y "Editar".
// =============================================================

public sealed partial class PanelAdmin : Page
{
    private const int ANIO_MINIMO_AUTO = 1950;


    // =========================================================
    // MOSTRAR VISTA
    // =========================================================

    private void MostrarAgregarElementos()
    {
        VistaInventario.Visibility = Visibility.Collapsed;
        VistaEditarProducto.Visibility = Visibility.Collapsed;
        VistaProductosRetirados.Visibility = Visibility.Collapsed;
        VistaEmpleados.Visibility = Visibility.Collapsed;
        VistaReportes.Visibility = Visibility.Collapsed;
        Formulario.Visibility = Visibility.Collapsed;

        VistaAgregarElementos.Visibility = Visibility.Visible;

        RefrescarListasElementos();
    }


    // =========================================================
    // AGREGAR AUTO
    // =========================================================

    private async void AgregarAuto_Click(
        object sender,
        RoutedEventArgs e)
    {
        string marcaAuto = LimpiarEspacios(TxtElemAutoMarca.Text);
        string modelo = LimpiarEspacios(TxtElemAutoModelo.Text);

        // ---------------- Validaciones ----------------

        if (string.IsNullOrWhiteSpace(marcaAuto) ||
            string.IsNullOrWhiteSpace(modelo))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe la marca y el modelo del auto."
            );
            return;
        }

        // Modelo: letras, números, espacios y guion (CR-V, Mazda 3)
        if (!Regex.IsMatch(modelo, @"^[\p{L}0-9 \-]+$"))
        {
            await MostrarMensaje(
                "Modelo no válido",
                "El modelo solo puede tener letras, números, espacios y guion (-)."
            );
            return;
        }

        int anioMaximo = DateTime.Now.Year + 1;

        if (!int.TryParse(TxtElemAutoAnioInicio.Text, out int anioInicio) ||
            !int.TryParse(TxtElemAutoAnioFin.Text, out int anioFin) ||
            anioInicio < ANIO_MINIMO_AUTO || anioInicio > anioMaximo ||
            anioFin < ANIO_MINIMO_AUTO || anioFin > anioMaximo)
        {
            await MostrarMensaje(
                "Años no válidos",
                $"Los años deben estar entre {ANIO_MINIMO_AUTO} y {anioMaximo}."
            );
            return;
        }

        if (anioInicio > anioFin)
        {
            await MostrarMensaje(
                "Años no válidos",
                "El año de inicio no puede ser mayor que el año de fin."
            );
            return;
        }

        // Si la marca del auto ya existe ("nissan" -> "Nissan"),
        // se usa la escritura que ya está registrada.
        string? marcaExistente = autos
            .Select(a => a.Marca)
            .FirstOrDefault(m => string.Equals(
                m, marcaAuto, StringComparison.OrdinalIgnoreCase));

        marcaAuto = marcaExistente ?? Capitalizar(marcaAuto);

        // Mismo auto con los mismos años = duplicado.
        // (Mismo modelo con OTROS años sí se permite: otra generación.)
        bool duplicado = autos.Any(a =>
            a.Marca.Equals(marcaAuto, StringComparison.OrdinalIgnoreCase) &&
            a.Modelo.Equals(modelo, StringComparison.OrdinalIgnoreCase) &&
            a.AnioInicio == anioInicio &&
            a.AnioFin == anioFin);

        if (duplicado)
        {
            await MostrarMensaje(
                "Auto repetido",
                $"{marcaAuto} {modelo} ({anioInicio}-{anioFin}) ya está registrado."
            );
            return;
        }

        // ---------------- Guardar ----------------

        ModeloAuto nuevo = new()
        {
            Marca = marcaAuto,
            Modelo = modelo,
            AnioInicio = anioInicio,
            AnioFin = anioFin
        };

        bool guardado = await GuardarElementoAsync(
            () => repoAutos.AddAsync(nuevo),
            "autos.json"
        );

        if (!guardado)
            return;

        // El repositorio ya asignó el Id. Se agrega a la colección
        // que usa LstFormAutos (lista de autos compatibles).
        autos.Add(nuevo);

        TxtElemAutoMarca.Text = string.Empty;
        TxtElemAutoModelo.Text = string.Empty;
        TxtElemAutoAnioInicio.Text = string.Empty;
        TxtElemAutoAnioFin.Text = string.Empty;

        RefrescarListasElementos();

        await MostrarMensaje(
            "Auto agregado",
            $"{nuevo.DescripcionCompleta} ya aparece en \"Autos compatibles\" al agregar o editar un producto."
        );
    }


    // =========================================================
    // AGREGAR MARCA DE PIEZA
    // =========================================================

    private async void AgregarMarca_Click(
        object sender,
        RoutedEventArgs e)
    {
        string nombre = LimpiarEspacios(TxtElemMarca.Text);

        if (string.IsNullOrWhiteSpace(nombre))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el nombre de la marca."
            );
            return;
        }

        if (marcas.Any(m => m.Nombre.Equals(
                nombre, StringComparison.OrdinalIgnoreCase)))
        {
            await MostrarMensaje(
                "Marca repetida",
                $"La marca \"{nombre}\" ya está registrada."
            );
            return;
        }

        Marca nueva = new()
        {
            Nombre = nombre
        };

        bool guardado = await GuardarElementoAsync(
            () => repoMarcas.AddAsync(nueva),
            "marcas.json"
        );

        if (!guardado)
            return;

        // Misma colección que usan CmbFormMarca y CmbMarca.
        marcas.Add(nueva);

        TxtElemMarca.Text = string.Empty;

        RefrescarListasElementos();

        await MostrarMensaje(
            "Marca agregada",
            $"\"{nueva.Nombre}\" ya aparece en la lista de marcas del producto."
        );
    }


    // =========================================================
    // AGREGAR CATEGORÍA
    // =========================================================

    private async void AgregarCategoria_Click(
        object sender,
        RoutedEventArgs e)
    {
        string nombre = LimpiarEspacios(TxtElemCategoria.Text);

        if (string.IsNullOrWhiteSpace(nombre))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el nombre de la categoría."
            );
            return;
        }

        nombre = Capitalizar(nombre, soloPrimera: true);

        if (categorias.Any(c => c.Nombre.Equals(
                nombre, StringComparison.OrdinalIgnoreCase)))
        {
            await MostrarMensaje(
                "Categoría repetida",
                $"La categoría \"{nombre}\" ya está registrada."
            );
            return;
        }

        Categoria nueva = new()
        {
            Nombre = nombre
        };

        bool guardado = await GuardarElementoAsync(
            () => repoCategorias.AddAsync(nueva),
            "categorias.json"
        );

        if (!guardado)
            return;

        // Misma colección que usa CmbFormCategoria.
        categorias.Add(nueva);

        TxtElemCategoria.Text = string.Empty;

        RefrescarListasElementos();

        await MostrarMensaje(
            "Categoría agregada",
            $"\"{nueva.Nombre}\" ya aparece en la lista de categorías del producto."
        );
    }


    // =========================================================
    // GUARDAR CON MANEJO DE ERRORES
    // =========================================================

    private async Task<bool> GuardarElementoAsync(
        Func<Task> guardar,
        string archivo)
    {
        try
        {
            await guardar();
            return true;
        }
        catch (Exception ex)
        {
            await MostrarMensaje(
                "No se pudo guardar",
                $"Ocurrió un error al escribir {archivo}.\n\n{ex.Message}"
            );
            return false;
        }
    }


    // =========================================================
    // REFRESCAR LISTAS (vista + filtros del inventario)
    // =========================================================

    private void RefrescarListasElementos()
    {
        // Listas de la vista "Agregar elementos"
        LstElemAutos.ItemsSource = autos
            .OrderBy(a => a.Marca)
            .ThenBy(a => a.Modelo)
            .ThenBy(a => a.AnioInicio)
            .ToList();

        LstElemMarcas.ItemsSource = marcas
            .OrderBy(m => m.Nombre)
            .ToList();

        LstElemCategorias.ItemsSource = categorias
            .OrderBy(c => c.Nombre)
            .ToList();

        TxtElemTotalAutos.Text = $"Autos registrados ({autos.Count})";
        TxtElemTotalMarcas.Text = $"Marcas registradas ({marcas.Count})";
        TxtElemTotalCategorias.Text = $"Categorías registradas ({categorias.Count})";

        // Filtros del inventario (se arman con .ToList(), por eso
        // no se actualizan solos como CmbFormMarca o LstFormAutos).
        CmbModelo.ItemsSource = autos
            .GroupBy(a => a.Id)
            .Select(g => g.First())
            .OrderBy(a => a.Modelo)
            .ToList();

        LstTipos.ItemsSource = categorias
            .Select(c => c.Nombre)
            .OrderBy(n => n)
            .ToList();
    }


    // =========================================================
    // UTILIDADES DE TEXTO
    // =========================================================

    private static string LimpiarEspacios(string? texto) =>
        Regex.Replace(texto ?? string.Empty, @"\s+", " ").Trim();

    // "nissan" -> "Nissan" | "sistema de clutch" -> "Sistema de clutch"
    private static string Capitalizar(
        string texto,
        bool soloPrimera = false)
    {
        if (string.IsNullOrEmpty(texto))
            return texto;

        if (soloPrimera)
            return char.ToUpper(texto[0], CultureInfo.CurrentCulture) + texto[1..];

        return CultureInfo.CurrentCulture.TextInfo.ToTitleCase(
            texto.ToLower(CultureInfo.CurrentCulture));
    }
}