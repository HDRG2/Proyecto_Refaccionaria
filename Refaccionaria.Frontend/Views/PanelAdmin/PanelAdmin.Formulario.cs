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
    private readonly List<int> autosCompatiblesSeleccionados = new();
    private void AutoCompatible_Checked(
    object sender,
    RoutedEventArgs e)
    {

        if (sender is not CheckBox check)
            return;

        if (check.DataContext is not ModeloAuto auto)
            return;

        if (!autosCompatiblesSeleccionados.Contains(auto.Id))
        {
            autosCompatiblesSeleccionados.Add(auto.Id);
        }

        ChkFormUniversal.IsChecked = false;
        ChkFormUniversal.IsEnabled = false;
    }

    private void AutoCompatible_Unchecked(
        object sender,
        RoutedEventArgs e)
    {

        if (sender is not CheckBox check)
            return;

        if (check.DataContext is not ModeloAuto auto)
            return;

        autosCompatiblesSeleccionados.Remove(auto.Id);

        if (autosCompatiblesSeleccionados.Count == 0)
        {
            ChkFormUniversal.IsEnabled = true;
        }
    }

    // =========================================================
    // UNIVERSAL
    // =========================================================

    private void Universal_Click(
    object sender,
    RoutedEventArgs e)
    {

        bool esUniversal =
            ChkFormUniversal.IsChecked == true;

        LstFormAutos.IsEnabled = !esUniversal;

        if (esUniversal)
        {
            autosCompatiblesSeleccionados.Clear();
        }
    }


    // =========================================================
    // CERRAR FORMULARIO
    // =========================================================

    private void CerrarFormulario_Click(
        object sender,
        RoutedEventArgs e)
    {
        Formulario.Visibility =
            Visibility.Collapsed;

        modoFormulario =
            string.Empty;

        refaccionEditando =
            null;

        usuarioEditando =
            null;
    }


    // =========================================================
    // GUARDAR
    // =========================================================

    private async void Guardar_Click(
        object sender,
        RoutedEventArgs e)
    {
        // =====================================================
        // NUEVO PRODUCTO
        // =====================================================

        if (modoFormulario == "NuevoProducto")
        {
            await GuardarNuevoProductoAsync();

            return;
        }

        // =====================================================
        // EDITAR PRODUCTO
        // =====================================================

        if (modoFormulario == "EditarProducto")
        {
            await GuardarEdicionProductoAsync();
            return;
        }

        //=====================================================
        // NUEVO EMPLEADO
        //=====================================================

        if (modoFormulario == "NuevoEmpleado")
        {
            await GuardarNuevoEmpleadoAsync();
            return;
        }

        //=====================================================
        // EDITAR EMPLEADO
        //=====================================================

        if (modoFormulario == "EditarEmpleado")
        {
            await GuardarEdicionEmpleadoAsync();
            return;
        }
    }

    // =========================================================
    // GUARDAR NUEVO PRODUCTO
    // =========================================================

    private async Task GuardarNuevoProductoAsync()
    {
        // =====================================================
        // 1. LEER DATOS DEL FORMULARIO
        // =====================================================

        string nombre =
            TxtFormNombre.Text.Trim();

        string codigo =
            TxtFormCodigo.Text.Trim();


        // =====================================================
        // 2. VALIDACIONES DE LA INTERFAZ
        // =====================================================

        if (string.IsNullOrWhiteSpace(nombre))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el nombre del producto."
            );

            TxtFormNombre.Focus(
                FocusState.Programmatic
            );

            return;
        }


        if (string.IsNullOrWhiteSpace(codigo))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el código del producto."
            );

            TxtFormCodigo.Focus(
                FocusState.Programmatic
            );

            return;
        }

        // Validar que nombre y código no tengan caracteres no permitidos
        string? errorProducto =
            Validaciones.RevisarProducto(nombre, codigo);

        if (errorProducto != null)
        {
            await MostrarMensaje(
                "Datos no válidos",
                errorProducto
            );

            return;
        }

        if (CmbFormCategoria.SelectedItem 
            is not Categoria categoria)
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Selecciona una categoría."
            );

            return;
        }


        if (CmbFormMarca.SelectedItem
            is not Marca marca)
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Selecciona una marca."
            );

            return;
        }


        // Código repetido: se bloquea. Nombre y marca repetidos: se avisa.
        if (!await RevisarRepetidosAsync(nombre, codigo, marca, null))
        {
            return;
        }


        if (!decimal.TryParse(
                TxtFormPrecio.Text.Trim(),
                out decimal precio)
            || precio < 0)
        {
            await MostrarMensaje(
                "Precio incorrecto",
                "Escribe un precio válido."
            );

            TxtFormPrecio.Focus(
                FocusState.Programmatic
            );

            return;
        }


        if (!int.TryParse(
                TxtFormStock.Text.Trim(),
                out int stock)
            || stock < 0)
        {
            await MostrarMensaje(
                "Stock incorrecto",
                "Escribe una cantidad válida."
            );

            TxtFormStock.Focus(
                FocusState.Programmatic
            );

            return;
        }


        // =====================================================
        // 3. COMPATIBILIDAD
        // =====================================================

        bool esUniversal =
            ChkFormUniversal.IsChecked == true;

        List<int> autosSeleccionados = new();

        if (!esUniversal)
        {
            autosSeleccionados.AddRange(
                autosCompatiblesSeleccionados
            );
        }


        try
        {
            // =================================================
            // 4. CREAR PRODUCTO MEDIANTE EL SERVICIO
            // =================================================

            Refaccion nuevaRefaccion =
                await productoService.CrearProductoAsync(
                    nombre,
                    codigo,
                    categoria,
                    marca,
                    precio,
                    stock,
                    esUniversal,
                    autosSeleccionados
                );


            // =================================================
            // 5. COMPLETAR INFORMACIÓN VISUAL
            // =================================================

            CompletarDatosRefaccion(
                nuevaRefaccion
            );


            // =================================================
            // 6. ACTUALIZAR COLECCIONES
            // =================================================

            todasLasRefacciones.Add(
                nuevaRefaccion
            );

            refacciones.Add(
                nuevaRefaccion
            );

            ListaTarjetas.ItemsSource =
                refacciones;

            ActualizarTodo();


            // =================================================
            // 7. CERRAR FORMULARIO
            // =================================================

            Formulario.Visibility =
                Visibility.Collapsed;

            modoFormulario =
                string.Empty;


            // =================================================
            // 8. CONFIRMACIÓN
            // =================================================

            await MostrarMensaje(
                "Producto guardado",
                $"La refacción \"{nuevaRefaccion.Nombre}\" se guardó correctamente."
            );
        }
        catch (Exception ex)
        {
            await MostrarMensaje(
                "No se pudo guardar el producto",
                ex.Message
            );
        }
    }

    private async Task GuardarEdicionProductoAsync()
    {
        // =====================================================
        // 1. COMPROBAR QUE HAY UN PRODUCTO EDITÁNDOSE
        // =====================================================

        if (refaccionEditando == null)
        {
            await MostrarMensaje(
                "Error",
                "No se encontró el producto que se desea editar."
            );

            return;
        }


        // =====================================================
        // 2. LEER DATOS DEL FORMULARIO
        // =====================================================

        string nombre =
            TxtFormNombre.Text.Trim();

        string codigo =
            TxtFormCodigo.Text.Trim();


        // =====================================================
        // 3. VALIDACIONES DE LA INTERFAZ
        // =====================================================

        if (string.IsNullOrWhiteSpace(nombre))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el nombre del producto."
            );

            TxtFormNombre.Focus(
                FocusState.Programmatic
            );

            return;
        }


        if (string.IsNullOrWhiteSpace(codigo))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el código del producto."
            );

            TxtFormCodigo.Focus(
                FocusState.Programmatic
            );

            return;
        }

        // Validar que nombre y código no tengan caracteres no permitidos
        string? errorProducto =
            Validaciones.RevisarProducto(nombre, codigo);

        if (errorProducto != null)
        {
            await MostrarMensaje(
                "Datos no válidos",
                errorProducto
            );

            return;
        }

        if (CmbFormCategoria.SelectedItem
            is not Categoria categoria)
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Selecciona una categoría."
            );

            return;
        }


        if (CmbFormMarca.SelectedItem
            is not Marca marca)
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Selecciona una marca."
            );

            return;
        }


        // Código repetido: se bloquea. Nombre y marca repetidos: se avisa.
        // La pieza que se está editando no se compara consigo misma.
        if (!await RevisarRepetidosAsync(nombre, codigo, marca, refaccionEditando))
        {
            return;
        }


        if (!decimal.TryParse(
                TxtFormPrecio.Text.Trim(),
                out decimal precio)
            || precio < 0)
        {
            await MostrarMensaje(
                "Precio incorrecto",
                "Escribe un precio válido."
            );

            TxtFormPrecio.Focus(
                FocusState.Programmatic
            );

            return;
        }


        if (!int.TryParse(
                TxtFormStock.Text.Trim(),
                out int stock)
            || stock < 0)
        {
            await MostrarMensaje(
                "Stock incorrecto",
                "Escribe una cantidad válida."
            );

            TxtFormStock.Focus(
                FocusState.Programmatic
            );

            return;
        }


        // =====================================================
        // 4. COMPATIBILIDAD
        // =====================================================

        bool esUniversal =
            ChkFormUniversal.IsChecked == true;

        List<int> autosSeleccionados = new();

        if (!esUniversal)
        {
            autosSeleccionados.AddRange(
                autosCompatiblesSeleccionados
            );
        }


        try
        {
            // =================================================
            // 5. EDITAR MEDIANTE PRODUCTOSERVICE
            // =================================================

            Refaccion productoActualizado =
                await productoService.EditarProductoAsync(
                    refaccionEditando,
                    nombre,
                    codigo,
                    categoria,
                    marca,
                    precio,
                    stock,
                    esUniversal,
                    autosSeleccionados
                );


            // =================================================
            // 6. COMPLETAR INFORMACIÓN VISUAL
            // =================================================

            CompletarDatosRefaccion(
                productoActualizado
            );


            // =================================================
            // 7. ACTUALIZAR COLECCIONES DE LA PANTALLA
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


            Refaccion? productoEnActivas =
                refacciones.FirstOrDefault(
                    r => r.Id == productoActualizado.Id
                );

            if (productoEnActivas != null &&
                !ReferenceEquals(
                    productoEnActivas,
                    productoActualizado))
            {
                int indice =
                    refacciones.IndexOf(
                        productoEnActivas
                    );

                refacciones[indice] =
                    productoActualizado;
            }


            // =================================================
            // 8. ACTUALIZAR PANTALLA
            // =================================================

            ActualizarTodo();


            // =================================================
            // 9. GUARDAR NOMBRE PARA EL MENSAJE
            // =================================================

            string nombreProducto =
                productoActualizado.Nombre;


            // =================================================
            // 10. CERRAR FORMULARIO
            // =================================================

            Formulario.Visibility =
                Visibility.Collapsed;

            modoFormulario =
                string.Empty;

            refaccionEditando =
                null;


            // =================================================
            // 11. CONFIRMACIÓN
            // =================================================

            await MostrarMensaje(
                "Producto actualizado",
                $"La refacción \"{nombreProducto}\" se actualizó correctamente."
            );
        }
        catch (Exception ex)
        {
            await MostrarMensaje(
                "No se pudo actualizar el producto",
                ex.Message
            );
        }
    }

    // =========================================================
    // REVISAR PIEZAS REPETIDAS
    // =========================================================
    // - Mismo código que otra pieza (activa o retirada): no se
    //   permite, porque la venta y el asistente se confunden.
    // - Mismo nombre y misma marca: se avisa y el administrador
    //   decide si la guarda (puede ser intencional).
    // Devuelve true si se puede continuar con el guardado.

    private static string NormalizarTexto(string texto) =>
        string.Join(
            " ",
            texto.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries)
        ).ToUpperInvariant();

    private async Task<bool> RevisarRepetidosAsync(
        string nombre,
        string codigo,
        Marca marca,
        Refaccion? excluir)
    {
        IEnumerable<Refaccion> otras =
            todasLasRefacciones.Where(
                r => excluir == null || r.Id != excluir.Id
            );


        // ----- CÓDIGO REPETIDO -----

        Refaccion? mismoCodigo =
            otras.FirstOrDefault(
                r => NormalizarTexto(r.Codigo ?? string.Empty) ==
                     NormalizarTexto(codigo)
            );

        if (mismoCodigo != null)
        {
            string estado =
                mismoCodigo.Activo ? "" : " (está en Productos retirados)";

            await MostrarMensaje(
                "Código repetido",
                $"El código {mismoCodigo.Codigo} ya lo tiene " +
                $"\"{mismoCodigo.Nombre}\"{estado}.\n\n" +
                "Cada pieza debe tener un código diferente."
            );

            TxtFormCodigo.Focus(FocusState.Programmatic);

            return false;
        }


        // ----- NOMBRE Y MARCA REPETIDOS -----

        Refaccion? mismoNombre =
            otras.FirstOrDefault(
                r => r.MarcaId == marca.Id &&
                     NormalizarTexto(r.Nombre ?? string.Empty) ==
                     NormalizarTexto(nombre)
            );

        if (mismoNombre == null)
        {
            return true;
        }

        string retirada =
            mismoNombre.Activo ? "" : "\n(Esa pieza está en Productos retirados.)";

        ContentDialog dialogo = new()
        {
            Title = "Pieza posiblemente repetida",

            Content =
                "Ya existe una pieza con el mismo nombre y marca:\n\n" +
                $"{mismoNombre.Codigo}  {mismoNombre.Nombre} ({marca.Nombre})" +
                retirada +
                "\n\n¿Deseas guardarla de todos modos?",

            PrimaryButtonText = "Guardar de todos modos",
            CloseButtonText = "Cancelar",
            DefaultButton = ContentDialogButton.Close,

            XamlRoot = XamlRoot
        };

        ContentDialogResult resultado =
            await dialogo.ShowAsync();

        if (resultado != ContentDialogResult.Primary)
        {
            TxtFormNombre.Focus(FocusState.Programmatic);
            return false;
        }

        return true;
    }
}
