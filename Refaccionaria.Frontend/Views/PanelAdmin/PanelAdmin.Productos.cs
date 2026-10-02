using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Frontend.Models;
using Windows.Networking.NetworkOperators;

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
        ChkFormUniversal.IsEnabled = true;


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

    private void AbrirProductoParaEditar(
    Refaccion refaccion)
    {
        refaccionEditando = refaccion;

        modoFormulario = "EditarProducto";

        // -----------------------------------------------------
        // MOSTRAR FORMULARIO
        // -----------------------------------------------------

        CamposEmpleado.Visibility = Visibility.Collapsed;
        CamposProducto.Visibility = Visibility.Visible;
        Formulario.Visibility = Visibility.Visible;

        TxtTituloFormulario.Text =
            "Editar producto";

        BtnEliminarProducto.Visibility =
            Visibility.Visible;


        // -----------------------------------------------------
        // DATOS
        // -----------------------------------------------------

        TxtFormNombre.Text =
            refaccion.Nombre;

        TxtFormCodigo.Text =
            refaccion.Codigo;

        TxtFormPrecio.Text =
            refaccion.Precio.ToString();

        TxtFormStock.Text =
            refaccion.Stock.ToString();


        // -----------------------------------------------------
        // CATEGORÍA
        // -----------------------------------------------------

        CmbFormCategoria.SelectedItem =
            categorias.FirstOrDefault(
                c => c.Id == refaccion.CategoriaId
            );


        // -----------------------------------------------------
        // MARCA
        // -----------------------------------------------------

        CmbFormMarca.SelectedItem =
            marcas.FirstOrDefault(
                m => m.Id == refaccion.MarcaId
            );


        // -----------------------------------------------------
        // LIMPIAR SELECCIÓN ANTERIOR
        // -----------------------------------------------------

        autosCompatiblesSeleccionados.Clear();

        foreach (ModeloAuto auto in autos)
        {
            auto.Seleccionado = false;
        }

        LstFormAutos.IsEnabled = true;

        ChkFormUniversal.IsChecked = false;
        ChkFormUniversal.IsEnabled = true;

        // -----------------------------------------------------
        // CARGAR AUTOS GUARDADOS
        // -----------------------------------------------------

        if (!refaccion.EsUniversal &&
            refaccion.AutosCompatibles != null)
        {
            foreach (ModeloAuto auto in autos)
            {
                bool estaSeleccionado =
                    refaccion.AutosCompatibles.Contains(auto.Id);
                auto.Seleccionado = estaSeleccionado;

                if (estaSeleccionado)
                {
                    autosCompatiblesSeleccionados.Add(auto.Id);
                }
            }
        }
        // -----------------------------------------------------
        // UNIVERSAL
        // -----------------------------------------------------

        ChkFormUniversal.IsChecked =
            refaccion.EsUniversal;

        ChkFormUniversal.IsEnabled =
            autosCompatiblesSeleccionados.Count == 0;


        // -----------------------------------------------------
        // LISTA DE AUTOS
        // -----------------------------------------------------

        LstFormAutos.IsEnabled =
            !refaccion.EsUniversal;

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
        // =====================================================
        // 1. COMPROBAR PRODUCTO
        // =====================================================

        if (refaccionEditando == null)
        {
            await MostrarMensaje(
                "Producto no encontrado",
                "No hay ningún producto seleccionado."
            );

            return;
        }

        Refaccion producto = refaccionEditando;


        // =====================================================
        // 2. CONFIRMAR RETIRO
        // =====================================================

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

        ContentDialogResult resultado =
            await dialogo.ShowAsync();

        if (resultado != ContentDialogResult.Primary)
        {
            return;
        }


        try
        {
            // =================================================
            // 3. RETIRAR MEDIANTE PRODUCTOSERVICE
            // =================================================

            await productoService.RetirarProductoAsync(
                producto.Id
            );


            // =================================================
            // 4. ACTUALIZAR OBJETO LOCAL
            // =================================================

            producto.Activo = false;


            // =================================================
            // 5. MOVER A PRODUCTOS RETIRADOS
            // =================================================

            refacciones.Remove(producto);

            if (!refaccionesInactivas.Contains(producto))
            {
                refaccionesInactivas.Add(producto);
            }


            // =================================================
            // 6. CERRAR FORMULARIO
            // =================================================

            refaccionEditando = null;

            modoFormulario =
                string.Empty;

            Formulario.Visibility =
                Visibility.Collapsed;


            // =================================================
            // 7. ACTUALIZAR PANTALLA
            // =================================================

            ActualizarTodo();


            // =================================================
            // 8. CONFIRMACIÓN
            // =================================================

            await MostrarMensaje(
                "Producto retirado",
                $"\"{producto.Nombre}\" fue enviado a Productos retirados."
            );
        }
        catch (Exception ex)
        {
            await MostrarMensaje(
                "No se pudo retirar el producto",
                ex.Message
            );
        }
    }


    // =========================================================
    // REACTIVAR / REABASTECER PRODUCTO
    // =========================================================

    private async void ReactivarProducto_Click(
    object sender,
    RoutedEventArgs e)
    {
        // =====================================================
        // 1. OBTENER PRODUCTO
        // =====================================================

        if (sender is not Button boton ||
            boton.Tag is not Refaccion producto)
        {
            return;
        }


        // =====================================================
        // 2. PEDIR CANTIDAD RECIBIDA
        // =====================================================

        NumberBox cajaCantidad = new()
        {
            Header = "Cantidad recibida",
            Minimum = 0,
            Maximum = 1000000,
            Value = 0,
            SpinButtonPlacementMode =
                NumberBoxSpinButtonPlacementMode.Compact
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
                FontWeight =
                    Microsoft.UI.Text.FontWeights.Bold
            }
        );


        contenido.Children.Add(
            new TextBlock
            {
                Text =
                    $"Existencia actual: {producto.Stock} piezas"
            }
        );


        contenido.Children.Add(
            cajaCantidad
        );


        // =====================================================
        // 3. MOSTRAR CONFIRMACIÓN
        // =====================================================

        ContentDialog dialogo = new()
        {
            Title = "Reactivar / reabastecer producto",

            Content = contenido,

            PrimaryButtonText = "Reactivar",
            CloseButtonText = "Cancelar",

            DefaultButton =
                ContentDialogButton.Primary,

            XamlRoot = XamlRoot
        };


        ContentDialogResult resultado =
            await dialogo.ShowAsync();


        if (resultado != ContentDialogResult.Primary)
        {
            return;
        }


        // =====================================================
        // 4. VALIDAR CANTIDAD
        // =====================================================

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


        int cantidadRecibida =
            (int)cajaCantidad.Value;


        try
        {
            // =================================================
            // 5. REACTIVAR MEDIANTE PRODUCTOSERVICE
            // =================================================

            Refaccion productoActualizado =
                await productoService.ReactivarProductoAsync(
                    producto.Id,
                    cantidadRecibida
                );


            // =================================================
            // 6. COMPLETAR INFORMACIÓN VISUAL
            // =================================================

            CompletarDatosRefaccion(
                productoActualizado
            );


            // =================================================
            // 7. ACTUALIZAR COLECCIÓN GENERAL
            // =================================================

            Refaccion? productoEnTodas =
                todasLasRefacciones.FirstOrDefault(
                    r => r.Id == productoActualizado.Id
                );

            if (productoEnTodas != null &&
                !ReferenceEquals(
                    productoEnTodas,
                    productoActualizado))
            {
                int indice =
                    todasLasRefacciones.IndexOf(
                        productoEnTodas
                    );

                todasLasRefacciones[indice] =
                    productoActualizado;
            }


            // =================================================
            // 8. QUITAR DE PRODUCTOS RETIRADOS
            // =================================================

            Refaccion? productoRetirado =
                refaccionesInactivas.FirstOrDefault(
                    r => r.Id == productoActualizado.Id
                );

            if (productoRetirado != null)
            {
                refaccionesInactivas.Remove(
                    productoRetirado
                );
            }


            // =================================================
            // 9. REGRESAR AL INVENTARIO ACTIVO
            // =================================================

            Refaccion? productoActivo =
                refacciones.FirstOrDefault(
                    r => r.Id == productoActualizado.Id
                );

            if (productoActivo == null)
            {
                refacciones.Add(
                    productoActualizado
                );
            }


            // =================================================
            // 10. ACTUALIZAR PANTALLA
            // =================================================

            ActualizarTodo();


            // =================================================
            // 11. CONFIRMACIÓN
            // =================================================

            await MostrarMensaje(
                "Producto reactivado",

                cantidadRecibida > 0

                    ? $"\"{productoActualizado.Nombre}\" volvió al inventario con {productoActualizado.Stock} piezas."

                    : $"\"{productoActualizado.Nombre}\" volvió al inventario."
            );
        }
        catch (Exception ex)
        {
            await MostrarMensaje(
                "No se pudo reactivar el producto",
                ex.Message
            );
        }
    }
    // =========================================================
    // ELIMINAR DEFINITIVAMENTE
    // =========================================================

    private async void EliminarDefinitivamente_Click(
        object sender,
        RoutedEventArgs e)
    {
        // =====================================================
        // 1. OBTENER PRODUCTO
        // =====================================================

        if (sender is not Button boton ||
            boton.Tag is not Refaccion producto)
        {
            return;
        }


        // =====================================================
        // 2. CONFIRMAR ELIMINACIÓN
        // =====================================================

        ContentDialog dialogo = new()
        {
            Title = "Eliminar definitivamente",

            Content =
                $"¿Estás seguro de eliminar \"{producto.Nombre}\"?\n\n" +
                "Esta acción borrará permanentemente el producto y no se puede deshacer.",

            PrimaryButtonText = "Eliminar definitivamente",
            CloseButtonText = "Cancelar",

            DefaultButton =
                ContentDialogButton.Close,

            XamlRoot = XamlRoot
        };


        ContentDialogResult resultado =
            await dialogo.ShowAsync();


        if (resultado != ContentDialogResult.Primary)
        {
            return;
        }


        try
        {
            // =================================================
            // 3. ELIMINAR MEDIANTE PRODUCTOSERVICE
            // =================================================

            await productoService.EliminarProductoAsync(
                producto.Id
            );


            // =================================================
            // 4. QUITAR DE PRODUCTOS RETIRADOS
            // =================================================

            Refaccion? productoRetirado =
                refaccionesInactivas.FirstOrDefault(
                    r => r.Id == producto.Id
                );

            if (productoRetirado != null)
            {
                refaccionesInactivas.Remove(
                    productoRetirado
                );
            }


            // =================================================
            // 5. QUITAR DEL INVENTARIO ACTIVO
            // =================================================

            Refaccion? productoActivo =
                refacciones.FirstOrDefault(
                    r => r.Id == producto.Id
                );

            if (productoActivo != null)
            {
                refacciones.Remove(
                    productoActivo
                );
            }


            // =================================================
            // 6. QUITAR DE LA COLECCIÓN GENERAL
            // =================================================

            Refaccion? productoGeneral =
                todasLasRefacciones.FirstOrDefault(
                    r => r.Id == producto.Id
                );

            if (productoGeneral != null)
            {
                todasLasRefacciones.Remove(
                    productoGeneral
                );
            }


            // =================================================
            // 7. ACTUALIZAR PANTALLA
            // =================================================

            ActualizarTodo();


            // =================================================
            // 8. CONFIRMACIÓN
            // =================================================

            await MostrarMensaje(
                "Producto eliminado",
                $"\"{producto.Nombre}\" fue eliminado definitivamente."
            );
        }
        catch (Exception ex)
        {
            await MostrarMensaje(
                "No se pudo eliminar el producto",
                ex.Message
            );
        }
    }
}