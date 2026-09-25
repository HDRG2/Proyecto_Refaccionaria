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
    // NUEVO PRODUCTO
    // =========================================================

    private void NuevoProducto_Click(
    object sender,
    RoutedEventArgs e)
    {
        modoFormulario = "NuevoProducto";

        refaccionEditando = null;
        usuarioEditando = null;

        // -----------------------------------------------------
        // MOSTRAR FORMULARIO
        // -----------------------------------------------------

        CamposEmpleado.Visibility = Visibility.Collapsed;

        CamposProducto.Visibility = Visibility.Visible;

        Formulario.Visibility = Visibility.Visible;


        // -----------------------------------------------------
        // TÍTULO
        // -----------------------------------------------------

        TxtTituloFormulario.Text =
            "Nuevo producto";


        // -----------------------------------------------------
        // OCULTAR ELIMINAR
        // -----------------------------------------------------

        BtnEliminarProducto.Visibility =
            Visibility.Collapsed;


        // -----------------------------------------------------
        // LIMPIAR CAMPOS
        // -----------------------------------------------------

        TxtFormNombre.Text =
            string.Empty;

        TxtFormCodigo.Text =
            string.Empty;

        TxtFormPrecio.Text =
            string.Empty;

        TxtFormStock.Text =
            string.Empty;


        // -----------------------------------------------------
        // SELECCIONAR CATEGORÍA Y MARCA POR DEFECTO
        // -----------------------------------------------------

        if (categorias.Count > 0)
        {
            CmbFormCategoria.SelectedIndex = 0;
        }

        if (marcas.Count > 0)
        {
            CmbFormMarca.SelectedIndex = 0;
        }


        // -----------------------------------------------------
        // UNIVERSAL
        // -----------------------------------------------------

        ChkFormUniversal.IsChecked = false;


        // -----------------------------------------------------
        // AUTOS
        // -----------------------------------------------------

        autosCompatiblesSeleccionados.Clear();

        LstFormAutos.IsEnabled = true;


        // -----------------------------------------------------
        // FOCUS
        // -----------------------------------------------------

        TxtFormNombre.Focus(
            FocusState.Programmatic
        );
    }


    // =========================================================
    // EDITAR PRODUCTO
    // =========================================================

    private void EditarProducto_Click(
    object sender,
    RoutedEventArgs e)
    {
        if (sender is Button boton &&
            boton.Tag is Refaccion refaccion)
        {
            AbrirProductoParaEditar(refaccion);
        }
    }

    private void AbrirProductoParaEditar(Refaccion refaccion)
    {
        // Guardamos qué producto estamos editando
        refaccionEditando = refaccion;

        modoFormulario = "EditarProducto";

        // Mostrar formulario de producto
        Formulario.Visibility = Visibility.Visible;
        CamposProducto.Visibility = Visibility.Visible;
        CamposEmpleado.Visibility = Visibility.Collapsed;

        TxtTituloFormulario.Text = "Editar producto";

        // Ahora sí mostramos el botón eliminar
        BtnEliminarProducto.Visibility = Visibility.Visible;

        // =====================================================
        // CARGAR LOS DATOS ACTUALES
        // =====================================================

        TxtFormNombre.Text = refaccion.Nombre;
        TxtFormCodigo.Text = refaccion.Codigo;
        TxtFormPrecio.Text = refaccion.Precio.ToString();
        TxtFormStock.Text = refaccion.Stock.ToString();

        // =====================================================
        // CATEGORÍA
        // =====================================================

        CmbFormCategoria.SelectedItem =
            categorias.FirstOrDefault(
                c => c.Id == refaccion.CategoriaId
            );

        // =====================================================
        // MARCA
        // =====================================================

        CmbFormMarca.SelectedItem =
            marcas.FirstOrDefault(
                m => m.Id == refaccion.MarcaId
            );

        // =====================================================
        // UNIVERSAL
        // =====================================================

        ChkFormUniversal.IsChecked =
            refaccion.EsUniversal;

        autosCompatiblesSeleccionados.Clear();

        LstFormAutos.IsEnabled =
            !refaccion.EsUniversal;

        // =====================================================
        // AUTOS COMPATIBLES
        // =====================================================

        if (!refaccion.EsUniversal &&
            refaccion.AutosCompatibles != null)
        {
            foreach (int autoId in refaccion.AutosCompatibles)
            {
                if (!autosCompatiblesSeleccionados.Contains(autoId))
                {
                    autosCompatiblesSeleccionados.Add(autoId);
                }
            }
        }
    }

    // =========================================================
    // EDITAR PRODUCTO DESDE LA VISTA "EDITAR PRODUCTO"
    // =========================================================

    private void EditarProductoDesdeLista_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (sender is Button boton &&
            boton.Tag is Refaccion refaccion)
        {
            AbrirProductoParaEditar(refaccion);
        }
    }


    // =========================================================
    // BUSCADOR DE LA VISTA "EDITAR PRODUCTO"
    // =========================================================

    private void BuscarEditar_TextChanged(
        object sender,
        TextChangedEventArgs e)
    {
        ActualizarListaEditar();
    }


    // =========================================================
    // ESTADO VACÍO DE LA VISTA "EDITAR PRODUCTO"
    // =========================================================

    private void ActualizarEstadoListaEditar()
    {
        int cantidad = 0;

        if (ListaEditarProductos.ItemsSource
            is System.Collections.IEnumerable elementos)
        {
            foreach (object _ in elementos)
            {
                cantidad++;
            }
        }

        ListaEditarProductos.Visibility =
            cantidad > 0
                ? Visibility.Visible
                : Visibility.Collapsed;

        PanelSinProductosEditar.Visibility =
            cantidad == 0
                ? Visibility.Visible
                : Visibility.Collapsed;
    }


    // =========================================================
    // ELIMINAR PRODUCTO
    // =========================================================

    private async void EliminarProductoDesdeFormulario_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (refaccionEditando == null)
        {
            await MostrarMensaje(
                "Producto no encontrado",
                "No hay ningún producto seleccionado."
            );
            return;
        }

        Refaccion producto = refaccionEditando;

        ContentDialog dialogo = new()
        {
            Title = "Retirar producto",
            Content =
                $"¿Deseas retirar \"{producto.Nombre}\" del inventario?\n\n" +
                "No se eliminará su información. Podrás reactivarlo después " +
                "desde Productos retirados.",
            PrimaryButtonText = "Retirar",
            CloseButtonText = "Cancelar",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = XamlRoot
        };

        ContentDialogResult resultado = await dialogo.ShowAsync();

        if (resultado != ContentDialogResult.Primary)
            return;

        producto.Activo = false;

        await repoRefacciones.UpdateAsync(producto);

        refacciones.Remove(producto);

        if (!refaccionesInactivas.Contains(producto))
            refaccionesInactivas.Add(producto);

        refaccionEditando = null;
        modoFormulario = string.Empty;
        Formulario.Visibility = Visibility.Collapsed;

        ActualizarTodo();

        await MostrarMensaje(
            "Producto retirado",
            $"\"{producto.Nombre}\" fue enviado a Productos retirados."
        );
    }


    // =========================================================
    // REACTIVAR / REABASTECER PRODUCTO
    // =========================================================

    private async void ReactivarProducto_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (sender is not Button boton ||
            boton.Tag is not Refaccion producto)
        {
            return;
        }

        NumberBox cajaCantidad = new()
        {
            Header = "Cantidad recibida",
            Minimum = 0,
            Maximum = 1000000,
            Value = 0,
            SpinButtonPlacementMode = NumberBoxSpinButtonPlacementMode.Compact
        };

        StackPanel contenido = new()
        {
            Spacing = 12
        };

        contenido.Children.Add(
            new TextBlock
            {
                Text = producto.Nombre,
                FontSize = 18,
                FontWeight = Microsoft.UI.Text.FontWeights.Bold
            }
        );

        contenido.Children.Add(
            new TextBlock
            {
                Text = $"Existencia actual: {producto.Stock} piezas"
            }
        );

        contenido.Children.Add(cajaCantidad);

        ContentDialog dialogo = new()
        {
            Title = "Reactivar / reabastecer producto",
            Content = contenido,
            PrimaryButtonText = "Reactivar",
            CloseButtonText = "Cancelar",
            DefaultButton = ContentDialogButton.Primary,
            XamlRoot = XamlRoot
        };

        ContentDialogResult resultado = await dialogo.ShowAsync();

        if (resultado != ContentDialogResult.Primary)
            return;

        if (double.IsNaN(cajaCantidad.Value) ||
            cajaCantidad.Value < 0 ||
            cajaCantidad.Value > int.MaxValue)
        {
            await MostrarMensaje(
                "Cantidad incorrecta",
                "Escribe una cantidad válida."
            );
            return;
        }

        int cantidadRecibida = (int)cajaCantidad.Value;

        producto.Stock += cantidadRecibida;
        producto.Activo = true;
        producto.StockBajo = producto.Stock <= 5;

        await repoRefacciones.UpdateAsync(producto);

        refaccionesInactivas.Remove(producto);

        if (!refacciones.Contains(producto))
            refacciones.Add(producto);

        ActualizarTodo();

        await MostrarMensaje(
            "Producto reactivado",
            cantidadRecibida > 0
                ? $"\"{producto.Nombre}\" volvió al inventario con {producto.Stock} piezas."
                : $"\"{producto.Nombre}\" volvió al inventario."
        );
    }


    // =========================================================
    // ELIMINAR DEFINITIVAMENTE
    // =========================================================

    private async void EliminarDefinitivamente_Click(
        object sender,
        RoutedEventArgs e)
    {
        if (sender is not Button boton ||
            boton.Tag is not Refaccion producto)
        {
            return;
        }

        ContentDialog dialogo = new()
        {
            Title = "Eliminar definitivamente",
            Content =
                $"¿Estás seguro de eliminar \"{producto.Nombre}\"?\n\n" +
                "Esta acción borrará permanentemente el producto y no se puede deshacer.",
            PrimaryButtonText = "Eliminar definitivamente",
            CloseButtonText = "Cancelar",
            DefaultButton = ContentDialogButton.Close,
            XamlRoot = XamlRoot
        };

        ContentDialogResult resultado = await dialogo.ShowAsync();

        if (resultado != ContentDialogResult.Primary)
            return;

        await repoRefacciones.DeleteAsync(producto.Id);

        refaccionesInactivas.Remove(producto);
        refacciones.Remove(producto);
        todasLasRefacciones.Remove(producto);

        ActualizarTodo();

        await MostrarMensaje(
            "Producto eliminado",
            $"\"{producto.Nombre}\" fue eliminado definitivamente."
        );
    }
}