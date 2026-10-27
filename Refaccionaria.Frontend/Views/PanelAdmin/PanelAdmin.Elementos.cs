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
// AGREGAR / EDITAR ELEMENTOS
//
// Registra o corrige autos (autos.json), marcas de piezas
// (marcas.json) y categorías (categorias.json).

// Al EDITAR solo cambia el nombre: el Id se conserva, por eso
// los productos y las ventas que ya usan ese auto, marca o
// categoría siguen ligados y muestran el nombre corregido.
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

        LimpiarCamposAuto();
        LimpiarCamposMarca();
        LimpiarCamposCategoria();

        RefrescarListasElementos();
    }


    // #########################################################
    //                          AUTOS
    // #########################################################

    // ---------------------------------------------------------
    // AGREGAR AUTO
    // ---------------------------------------------------------

    private async void AgregarAuto_Click(
        object sender,
        RoutedEventArgs e)
    {
        var datos = await LeerDatosAutoAsync(idExcluir: 0);

        if (!datos.Ok)
            return;

        ModeloAuto nuevo = new()
        {
            Marca = datos.Marca,
            Modelo = datos.Modelo,
            AnioInicio = datos.Inicio,
            AnioFin = datos.Fin
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

        LimpiarCamposAuto();
        RefrescarListasElementos();

        await MostrarMensaje(
            "Auto agregado",
            $"{nuevo.DescripcionCompleta} ya aparece en \"Autos compatibles\" al agregar o editar un producto."
        );
    }


    // ---------------------------------------------------------
    // EDITAR AUTO
    // ---------------------------------------------------------

    private async void EditarAuto_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (LstElemAutos.SelectedItem is not ModeloAuto auto)
        {
            await MostrarMensaje(
                "Selecciona un auto",
                "Primero elige en la lista el auto que quieres corregir."
            );
            return;
        }

        var datos = await LeerDatosAutoAsync(idExcluir: auto.Id);

        if (!datos.Ok)
            return;

        bool sinCambios =
            auto.Marca == datos.Marca &&
            auto.Modelo == datos.Modelo &&
            auto.AnioInicio == datos.Inicio &&
            auto.AnioFin == datos.Fin;

        if (sinCambios)
        {
            await MostrarMensaje(
                "Sin cambios",
                "No modificaste ningún dato del auto."
            );
            return;
        }

        string antes = auto.DescripcionCompleta;

        // Guardar valores anteriores por si falla la escritura
        string marcaAnterior = auto.Marca;
        string modeloAnterior = auto.Modelo;
        int inicioAnterior = auto.AnioInicio;
        int finAnterior = auto.AnioFin;

        auto.Marca = datos.Marca;
        auto.Modelo = datos.Modelo;
        auto.AnioInicio = datos.Inicio;
        auto.AnioFin = datos.Fin;

        bool guardado = await GuardarElementoAsync(
            () => repoAutos.UpdateAsync(auto),
            "autos.json"
        );

        if (!guardado)
        {
            auto.Marca = marcaAnterior;
            auto.Modelo = modeloAnterior;
            auto.AnioInicio = inicioAnterior;
            auto.AnioFin = finAnterior;
            return;
        }

        LimpiarCamposAuto();
        RefrescarTrasEdicion();

        await MostrarMensaje(
            "Auto actualizado",
            $"{antes}  →  {auto.DescripcionCompleta}\n\n" +
            "Los productos compatibles con este auto ya muestran el dato corregido."
        );
    }


    // ---------------------------------------------------------
    // ELEGIR AUTO DE LA LISTA (carga sus datos para editar)
    // ---------------------------------------------------------

    private void ElemAuto_SelectionChanged(
        object sender,
        SelectionChangedEventArgs e)
    {
        if (LstElemAutos.SelectedItem is not ModeloAuto auto)
        {
            BtnEditarAuto.IsEnabled = false;
            return;
        }

        TxtElemAutoMarca.Text = auto.Marca;
        TxtElemAutoModelo.Text = auto.Modelo;
        TxtElemAutoAnioInicio.Text = auto.AnioInicio.ToString();
        TxtElemAutoAnioFin.Text = auto.AnioFin.ToString();

        BtnEditarAuto.IsEnabled = true;
    }


    // ---------------------------------------------------------
    // LEER Y VALIDAR DATOS DEL AUTO
    //
    // idExcluir = 0 al agregar; al editar es el Id del auto
    // que se corrige (para no marcarlo como duplicado de sí mismo).
    // ---------------------------------------------------------

    private async Task<(bool Ok, string Marca, string Modelo, int Inicio, int Fin)>
        LeerDatosAutoAsync(int idExcluir)
    {
        var fallo = (false, string.Empty, string.Empty, 0, 0);

        string marcaAuto = LimpiarEspacios(TxtElemAutoMarca.Text);
        string modelo = LimpiarEspacios(TxtElemAutoModelo.Text);

        if (string.IsNullOrWhiteSpace(marcaAuto) ||
            string.IsNullOrWhiteSpace(modelo))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe la marca y el modelo del auto."
            );
            return fallo;
        }

        // Marca del auto: solo letras y espacios
        if (!Validaciones.EsLetras(marcaAuto))
        {
            await MostrarMensaje(
                "Marca no válida",
                "La marca del auto solo puede tener letras."
            );
            return fallo;
        }

        // Modelo: la MISMA regla que la caja de texto
        // (Validaciones.ModeloAuto): letras, números, espacios,
        // guion y punto ("X-Trail", "CR-V", "CX-5", "Serie 3").
        // Debe llevar al menos una letra o número ("-" solo no vale).
        if (!Validaciones.EsModeloAuto(modelo) ||
            !modelo.Any(char.IsLetterOrDigit))
        {
            await MostrarMensaje(
                "Modelo no válido",
                "El modelo solo puede tener letras, números, espacios, " +
                "guion (-) y punto (.). Por ejemplo: X-Trail, CR-V o Serie 3."
            );
            return fallo;
        }

        // "focus" -> "Focus" (solo la primera letra; "CX-5" no cambia).
        modelo = Capitalizar(modelo, soloPrimera: true);

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
            return fallo;
        }

        if (anioInicio > anioFin)
        {
            await MostrarMensaje(
                "Años no válidos",
                "El año de inicio no puede ser mayor que el año de fin."
            );
            return fallo;
        }

        // Si la marca del auto ya existe en OTRO auto ("nissan" ->
        // "Nissan"), se usa la escritura que ya está registrada.
        string? marcaExistente = autos
            .Where(a => a.Id != idExcluir)
            .Select(a => a.Marca)
            .FirstOrDefault(m => string.Equals(
                m, marcaAuto, StringComparison.OrdinalIgnoreCase));

        marcaAuto = marcaExistente ?? Capitalizar(marcaAuto);

        // Mismo auto con los mismos años = duplicado.
        // (Mismo modelo con OTROS años sí se permite: otra generación.)
        bool duplicado = autos.Any(a =>
            a.Id != idExcluir &&
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
            return fallo;
        }

        return (true, marcaAuto, modelo, anioInicio, anioFin);
    }


    private void LimpiarCamposAuto()
    {
        TxtElemAutoMarca.Text = string.Empty;
        TxtElemAutoModelo.Text = string.Empty;
        TxtElemAutoAnioInicio.Text = string.Empty;
        TxtElemAutoAnioFin.Text = string.Empty;

        LstElemAutos.SelectedItem = null;
        BtnEditarAuto.IsEnabled = false;
    }


    // #########################################################
    //                    MARCAS DE PIEZAS
    // #########################################################

    // ---------------------------------------------------------
    // AGREGAR MARCA
    // ---------------------------------------------------------

    private async void AgregarMarca_Click(
        object sender,
        RoutedEventArgs e)
    {
        string? nombre = await LeerNombreMarcaAsync(idExcluir: 0);

        if (nombre == null)
            return;

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

        LimpiarCamposMarca();
        RefrescarListasElementos();

        await MostrarMensaje(
            "Marca agregada",
            $"\"{nueva.Nombre}\" ya aparece en la lista de marcas del producto."
        );
    }


    // ---------------------------------------------------------
    // EDITAR MARCA
    // ---------------------------------------------------------

    private async void EditarMarca_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (LstElemMarcas.SelectedItem is not Marca marca)
        {
            await MostrarMensaje(
                "Selecciona una marca",
                "Primero elige en la lista la marca que quieres corregir."
            );
            return;
        }

        string? nombre = await LeerNombreMarcaAsync(idExcluir: marca.Id);

        if (nombre == null)
            return;

        if (nombre == marca.Nombre)
        {
            await MostrarMensaje(
                "Sin cambios",
                "No modificaste el nombre de la marca."
            );
            return;
        }

        string anterior = marca.Nombre;

        marca.Nombre = nombre;

        bool guardado = await GuardarElementoAsync(
            () => repoMarcas.UpdateAsync(marca),
            "marcas.json"
        );

        if (!guardado)
        {
            marca.Nombre = anterior;
            return;
        }

        LimpiarCamposMarca();
        RefrescarTrasEdicion();

        int productos = todasLasRefacciones.Count(r => r.MarcaId == marca.Id);

        await MostrarMensaje(
            "Marca actualizada",
            $"\"{anterior}\"  →  \"{marca.Nombre}\"\n\n" +
            $"{productos} producto(s) de esta marca ya muestran el nombre corregido."
        );
    }


    private void ElemMarca_SelectionChanged(
        object sender,
        SelectionChangedEventArgs e)
    {
        if (LstElemMarcas.SelectedItem is not Marca marca)
        {
            BtnEditarMarca.IsEnabled = false;
            return;
        }

        TxtElemMarca.Text = marca.Nombre;

        BtnEditarMarca.IsEnabled = true;
    }


    // Devuelve el nombre válido, o null si hubo un problema
    // (el mensaje ya se mostró).
    private async Task<string?> LeerNombreMarcaAsync(int idExcluir)
    {
        string nombre = LimpiarEspacios(TxtElemMarca.Text);

        if (string.IsNullOrWhiteSpace(nombre))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el nombre de la marca."
            );
            return null;
        }

        // Marca de pieza: solo letras y espacios (sin números)
        if (!Validaciones.EsLetras(nombre))
        {
            await MostrarMensaje(
                "Marca no válida",
                "El nombre de la marca solo puede tener letras. " +
                "No se aceptan números ni caracteres especiales."
            );
            return null;
        }

        if (marcas.Any(m =>
                m.Id != idExcluir &&
                m.Nombre.Equals(nombre, StringComparison.OrdinalIgnoreCase)))
        {
            await MostrarMensaje(
                "Marca repetida",
                $"La marca \"{nombre}\" ya está registrada."
            );
            return null;
        }

        return nombre;
    }


    private void LimpiarCamposMarca()
    {
        TxtElemMarca.Text = string.Empty;

        LstElemMarcas.SelectedItem = null;
        BtnEditarMarca.IsEnabled = false;
    }


    // #########################################################
    //                       CATEGORÍAS
    // #########################################################

    // ---------------------------------------------------------
    // AGREGAR CATEGORÍA
    // ---------------------------------------------------------

    private async void AgregarCategoria_Click(
        object sender,
        RoutedEventArgs e)
    {
        string? nombre = await LeerNombreCategoriaAsync(idExcluir: 0);

        if (nombre == null)
            return;

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

        LimpiarCamposCategoria();
        RefrescarListasElementos();

        await MostrarMensaje(
            "Categoría agregada",
            $"\"{nueva.Nombre}\" ya aparece en la lista de categorías del producto."
        );
    }


    // ---------------------------------------------------------
    // EDITAR CATEGORÍA
    // ---------------------------------------------------------

    private async void EditarCategoria_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (LstElemCategorias.SelectedItem is not Categoria categoria)
        {
            await MostrarMensaje(
                "Selecciona una categoría",
                "Primero elige en la lista la categoría que quieres corregir."
            );
            return;
        }

        string? nombre = await LeerNombreCategoriaAsync(idExcluir: categoria.Id);

        if (nombre == null)
            return;

        if (nombre == categoria.Nombre)
        {
            await MostrarMensaje(
                "Sin cambios",
                "No modificaste el nombre de la categoría."
            );
            return;
        }

        string anterior = categoria.Nombre;

        categoria.Nombre = nombre;

        bool guardado = await GuardarElementoAsync(
            () => repoCategorias.UpdateAsync(categoria),
            "categorias.json"
        );

        if (!guardado)
        {
            categoria.Nombre = anterior;
            return;
        }

        LimpiarCamposCategoria();
        RefrescarTrasEdicion();

        int productos = todasLasRefacciones.Count(r => r.CategoriaId == categoria.Id);

        await MostrarMensaje(
            "Categoría actualizada",
            $"\"{anterior}\"  →  \"{categoria.Nombre}\"\n\n" +
            $"{productos} producto(s) de esta categoría ya muestran el nombre corregido."
        );
    }


    private void ElemCategoria_SelectionChanged(
        object sender,
        SelectionChangedEventArgs e)
    {
        if (LstElemCategorias.SelectedItem is not Categoria categoria)
        {
            BtnEditarCategoria.IsEnabled = false;
            return;
        }

        TxtElemCategoria.Text = categoria.Nombre;

        BtnEditarCategoria.IsEnabled = true;
    }


    private async Task<string?> LeerNombreCategoriaAsync(int idExcluir)
    {
        string nombre = LimpiarEspacios(TxtElemCategoria.Text);

        if (string.IsNullOrWhiteSpace(nombre))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el nombre de la categoría."
            );
            return null;
        }

        if (!Validaciones.EsLetras(nombre))
        {
            await MostrarMensaje(
                "Categoría no válida",
                "El nombre de la categoría solo puede tener letras."
            );
            return null;
        }

        nombre = Capitalizar(nombre, soloPrimera: true);

        if (categorias.Any(c =>
                c.Id != idExcluir &&
                c.Nombre.Equals(nombre, StringComparison.OrdinalIgnoreCase)))
        {
            await MostrarMensaje(
                "Categoría repetida",
                $"La categoría \"{nombre}\" ya está registrada."
            );
            return null;
        }

        return nombre;
    }


    private void LimpiarCamposCategoria()
    {
        TxtElemCategoria.Text = string.Empty;

        LstElemCategorias.SelectedItem = null;
        BtnEditarCategoria.IsEnabled = false;
    }


    // #########################################################
    //                      COMPARTIDO
    // #########################################################

    // ---------------------------------------------------------
    // GUARDAR CON MANEJO DE ERRORES
    // ---------------------------------------------------------

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


    // ---------------------------------------------------------
    // REFRESCAR LISTAS (vista + filtros del inventario)
    // ---------------------------------------------------------

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


    // ---------------------------------------------------------
    // REFRESCAR TODO DESPUÉS DE EDITAR UN NOMBRE
    //
    // Los productos guardan el Id, pero en pantalla muestran el
    // nombre (MarcaNombre, CategoriaNombre, AutosDescripciones).
    // Se recalculan para que las tarjetas muestren lo corregido.
    // ---------------------------------------------------------

    private void RefrescarTrasEdicion()
    {
        foreach (Refaccion refaccion in todasLasRefacciones)
        {
            CompletarDatosRefaccion(refaccion);
        }

        // Volver a asignar las fuentes obliga a redibujar los
        // nombres en los combos y en la lista de autos compatibles.
        CmbFormMarca.ItemsSource = null;
        CmbFormMarca.ItemsSource = marcas;

        CmbFormCategoria.ItemsSource = null;
        CmbFormCategoria.ItemsSource = categorias;

        LstFormAutos.ItemsSource = null;
        LstFormAutos.ItemsSource = autos;

        CmbMarca.ItemsSource = null;
        CmbMarca.ItemsSource = marcas;

        ListaProductosRetirados.ItemsSource = null;

        RefrescarListasElementos();

        ActualizarTodo();

        AplicarFiltrosInventario();
    }


    // ---------------------------------------------------------
    // UTILIDADES DE TEXTO
    // ---------------------------------------------------------

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