using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Frontend.Models;

namespace Refaccionaria.Frontend.Views;

public sealed partial class PanelAdmin : Page
{
    // =========================================================
    // FILTROS
    // =========================================================

    private void BotonFiltros_Cambio(
    object sender,
    RoutedEventArgs e)
    {
        PanelFiltros.Visibility =
            BotonFiltros.IsChecked == true
                ? Visibility.Visible
                : Visibility.Collapsed;
    }


    private void LimpiarFiltros_Click(
     object sender,
     RoutedEventArgs e)
    {
        CmbMarca.SelectedIndex = -1;
        CmbModelo.SelectedIndex = -1;
        LstTipos.SelectedIndex = -1;

        TxtBuscar.Text = "";

        AplicarFiltrosInventario();
    }


    private void Orden_SelectionChanged(
        object sender,
        SelectionChangedEventArgs e)
    {
        AplicarFiltrosInventario();
    }


    private void Marca_SelectionChanged(
        object sender,
        SelectionChangedEventArgs e)
    {
        AplicarFiltrosInventario();
    }


    private void Filtro_Changed(
     object sender,
     SelectionChangedEventArgs e)
    {
        if (LstTipos != null)
        {
            ActualizarColoresCategorias();
        }

        AplicarFiltrosInventario();
    }


    private void Buscar_TextChanged(
        object sender,
        TextChangedEventArgs e)
    {
        AplicarFiltrosInventario();
    }

    private void AplicarFiltrosInventario()
    {
        // =========================================================
        // VALIDAR QUE LOS CONTROLES ESTÉN INICIALIZADOS
        // =========================================================

        if (CmbMarca == null ||
            CmbModelo == null ||
            LstTipos == null ||
            TxtBuscar == null ||
            CmbOrden == null ||
            ListaTarjetas == null)
        {
            return;
        }

        // =========================================================
        // OBTENER FILTROS SELECCIONADOS
        // =========================================================

        var marca = CmbMarca.SelectedItem as Marca;
        var modelo = CmbModelo.SelectedItem as ModeloAuto;
        var categoria = LstTipos.SelectedItem as string;

        string busqueda = TxtBuscar.Text?.Trim() ?? "";

        IEnumerable<Refaccion> resultado = refacciones;

        if (marca != null)
        {
            resultado = resultado.Where(r =>
                r.MarcaId == marca.Id);
        }

        if (modelo != null)
        {
            resultado = resultado.Where(r =>
                r.EsUniversal ||
                (r.AutosCompatibles != null &&
                 r.AutosCompatibles.Any(id =>
                     autos.Any(a =>
                         a.Id == id &&
                         a.Modelo == modelo.Modelo))));
        }

        if (!string.IsNullOrEmpty(categoria))
        {
            resultado = resultado.Where(r =>
                r.CategoriaNombre == categoria);
        }

        if (!string.IsNullOrWhiteSpace(busqueda))
        {
            resultado = resultado.Where(r =>
                (r.Nombre ?? "").Contains(
                    busqueda, StringComparison.OrdinalIgnoreCase) ||
                (r.Codigo ?? "").Contains(
                    busqueda, StringComparison.OrdinalIgnoreCase) ||
                (r.MarcaNombre ?? "").Contains(
                    busqueda, StringComparison.OrdinalIgnoreCase));
        }

        // =========================================================
        // ORDENAR RESULTADOS
        // =========================================================

        switch (CmbOrden.SelectedIndex)
        {
            case 1:
                // Nombre Z-A
                resultado = resultado.OrderByDescending(r => r.Nombre);
                break;

            case 2:
                // Precio menor a mayor
                resultado = resultado.OrderBy(r => r.Precio);
                break;

            case 3:
                // Precio mayor a menor
                resultado = resultado.OrderByDescending(r => r.Precio);
                break;

            case 4:
                // Menor existencia primero
                resultado = resultado.OrderBy(r => r.Stock);
                break;

            default:
                // Nombre A-Z
                resultado = resultado.OrderBy(r => r.Nombre);
                break;
        }

        // =========================================================
        // MOSTRAR RESULTADOS
        // =========================================================

        ListaTarjetas.ItemsSource = resultado.ToList();
    }

    private void ActualizarColoresCategorias()
    {
        if (LstTipos == null)
            return;

        foreach (var item in LstTipos.Items)
        {
            if (LstTipos.ContainerFromItem(item) is GridViewItem contenedor)
            {
                if (BuscarBordeCategoria(contenedor) is Border borde)
                {
                    bool seleccionado =
                        Equals(item, LstTipos.SelectedItem);

                    borde.Background =
                        new Microsoft.UI.Xaml.Media.SolidColorBrush(
                            seleccionado
                                ? Windows.UI.Color.FromArgb(255, 204, 9, 47)
                                : Windows.UI.Color.FromArgb(255, 255, 255, 255));

                    borde.BorderBrush =
                        new Microsoft.UI.Xaml.Media.SolidColorBrush(
                            seleccionado
                                ? Windows.UI.Color.FromArgb(255, 204, 9, 47)
                                : Windows.UI.Color.FromArgb(255, 213, 213, 213));

                    borde.BorderThickness = new Thickness(1);

                    if (borde.Child is TextBlock texto)
                    {
                        texto.Foreground =
                            new Microsoft.UI.Xaml.Media.SolidColorBrush(
                                seleccionado
                                    ? Windows.UI.Color.FromArgb(255, 255, 255, 255)
                                    : Windows.UI.Color.FromArgb(255, 41, 41, 41));
                    }
                }
            }
        }
    }

    private Border? BuscarBordeCategoria(DependencyObject elemento)
    {
        if (elemento is Border borde &&
            borde.Child is TextBlock)
        {
            return borde;
        }

        int cantidad =
            Microsoft.UI.Xaml.Media.VisualTreeHelper.GetChildrenCount(elemento);

        for (int i = 0; i < cantidad; i++)
        {
            var hijo =
                Microsoft.UI.Xaml.Media.VisualTreeHelper.GetChild(elemento, i);

            var encontrado = BuscarBordeCategoria(hijo);

            if (encontrado != null)
                return encontrado;
        }

        return null;
    }
}


