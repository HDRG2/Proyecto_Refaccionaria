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

        if (check.Tag is not int autoId)
            return;

        if (!autosCompatiblesSeleccionados.Contains(autoId))
        {
            autosCompatiblesSeleccionados.Add(autoId);
        }
    }


    private void AutoCompatible_Unchecked(
        object sender,
        RoutedEventArgs e)
    {
        if (sender is not CheckBox check)
            return;

        if (check.Tag is not int autoId)
            return;

        autosCompatiblesSeleccionados.Remove(autoId);
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
        // -----------------------------------------------------
        // NOMBRE
        // -----------------------------------------------------

        string nombre =
            TxtFormNombre.Text.Trim();

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


        // -----------------------------------------------------
        // CÓDIGO
        // -----------------------------------------------------

        string codigo =
            TxtFormCodigo.Text.Trim();

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


        // -----------------------------------------------------
        // CÓDIGO DUPLICADO
        // -----------------------------------------------------

        bool codigoExiste = todasLasRefacciones.Any(
            r => r.Codigo.Equals(
                codigo,
                StringComparison.OrdinalIgnoreCase
            )
        );

        if (codigoExiste)
        {
            await MostrarMensaje(
                "Código existente",
                "Ya existe una refacción con ese código."
            );

            TxtFormCodigo.Focus(
                FocusState.Programmatic
            );

            return;
        }


        // -----------------------------------------------------
        // CATEGORÍA
        // -----------------------------------------------------

        if (CmbFormCategoria.SelectedItem
            is not Categoria categoria)
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Selecciona una categoría."
            );

            return;
        }


        // -----------------------------------------------------
        // MARCA
        // -----------------------------------------------------

        if (CmbFormMarca.SelectedItem
            is not Marca marca)
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Selecciona una marca."
            );

            return;
        }


        // -----------------------------------------------------
        // PRECIO
        // -----------------------------------------------------

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


        // -----------------------------------------------------
        // STOCK
        // -----------------------------------------------------

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


        // -----------------------------------------------------
        // UNIVERSAL
        // -----------------------------------------------------

        bool esUniversal =
            ChkFormUniversal.IsChecked == true;


        // -----------------------------------------------------
        // AUTOS COMPATIBLES
        // -----------------------------------------------------

        List<int> autosSeleccionados = new();

        if (!esUniversal)
        {
            autosSeleccionados.AddRange(
                autosCompatiblesSeleccionados
            );
        }


        // -----------------------------------------------------
        // CREAR REFACCIÓN
        // -----------------------------------------------------

        Refaccion nuevaRefaccion =
            new()
            {
                Codigo = codigo,

                Nombre = nombre,

                MarcaId = marca.Id,

                CategoriaId = categoria.Id,

                Precio = precio,

                Stock = stock,

                StockBajo = stock <= 5,

                Activo = true,

                EsUniversal = esUniversal,

                AutosCompatibles =
                    autosSeleccionados,

                MarcaNombre =
                    marca.Nombre,

                CategoriaNombre =
                    categoria.Nombre
            };


        // -----------------------------------------------------
        // AUTOS PARA MOSTRAR EN LA TARJETA
        // -----------------------------------------------------

        if (!esUniversal)
        {
            foreach (
                int autoId
                in autosSeleccionados)
            {
                ModeloAuto? auto =
                    autos.FirstOrDefault(
                        a => a.Id == autoId
                    );

                if (auto != null)
                {
                    nuevaRefaccion
                        .AutosDescripciones
                        .Add(
                            auto.DescripcionCompleta
                        );
                }
            }
        }


        // -----------------------------------------------------
        // GUARDAR EN JSON
        // -----------------------------------------------------

        await repoRefacciones.AddAsync(
            nuevaRefaccion
        );


        // -----------------------------------------------------
        // AGREGAR A LA COLECCIÓN VISUAL
        // -----------------------------------------------------

        todasLasRefacciones.Add(
            nuevaRefaccion
        );

        refacciones.Add(
            nuevaRefaccion
        );


        // -----------------------------------------------------
        // ACTUALIZAR PANTALLA
        // -----------------------------------------------------

        ListaTarjetas.ItemsSource =
            refacciones;

        ActualizarTodo();


        // -----------------------------------------------------
        // CERRAR FORMULARIO
        // -----------------------------------------------------

        Formulario.Visibility =
            Visibility.Collapsed;

        modoFormulario =
            string.Empty;


        // -----------------------------------------------------
        // MENSAJE
        // -----------------------------------------------------

        await MostrarMensaje(
            "Producto guardado",
            $"La refacción \"{nuevaRefaccion.Nombre}\" se guardó correctamente."
        );
    }

    private async Task GuardarEdicionProductoAsync()
    {
        // =====================================================
        // COMPROBAR QUE HAY UN PRODUCTO EDITÁNDOSE
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
        // NOMBRE
        // =====================================================

        string nombre = TxtFormNombre.Text.Trim();

        if (string.IsNullOrWhiteSpace(nombre))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el nombre del producto."
            );

            TxtFormNombre.Focus(FocusState.Programmatic);

            return;
        }


        // =====================================================
        // CÓDIGO
        // =====================================================

        string codigo = TxtFormCodigo.Text.Trim();

        if (string.IsNullOrWhiteSpace(codigo))
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Escribe el código del producto."
            );

            TxtFormCodigo.Focus(FocusState.Programmatic);

            return;
        }


        // =====================================================
        // EVITAR CÓDIGOS DUPLICADOS
        // =====================================================

        bool codigoExiste = todasLasRefacciones.Any(
            r =>
                r.Id != refaccionEditando.Id &&
                r.Codigo.Equals(
                    codigo,
                    StringComparison.OrdinalIgnoreCase
                )
        );

        if (codigoExiste)
        {
            await MostrarMensaje(
                "Código existente",
                "Ya existe otra refacción con ese código."
            );

            TxtFormCodigo.Focus(FocusState.Programmatic);

            return;
        }


        // =====================================================
        // CATEGORÍA
        // =====================================================

        if (CmbFormCategoria.SelectedItem is not Categoria categoria)
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Selecciona una categoría."
            );

            return;
        }


        // =====================================================
        // MARCA
        // =====================================================

        if (CmbFormMarca.SelectedItem is not Marca marca)
        {
            await MostrarMensaje(
                "Datos incompletos",
                "Selecciona una marca."
            );

            return;
        }


        // =====================================================
        // PRECIO
        // =====================================================

        if (!decimal.TryParse(
                TxtFormPrecio.Text.Trim(),
                out decimal precio)
            || precio < 0)
        {
            await MostrarMensaje(
                "Precio incorrecto",
                "Escribe un precio válido."
            );

            TxtFormPrecio.Focus(FocusState.Programmatic);

            return;
        }


        // =====================================================
        // STOCK
        // =====================================================

        if (!int.TryParse(
                TxtFormStock.Text.Trim(),
                out int stock)
            || stock < 0)
        {
            await MostrarMensaje(
                "Stock incorrecto",
                "Escribe una cantidad válida."
            );

            TxtFormStock.Focus(FocusState.Programmatic);

            return;
        }


        // =====================================================
        // UNIVERSAL
        // =====================================================

        bool esUniversal =
            ChkFormUniversal.IsChecked == true;


        // =====================================================
        // AUTOS COMPATIBLES
        // =====================================================

        List<int> autosSeleccionados = new();

        if (!esUniversal)
        {
            autosSeleccionados.AddRange(
                autosCompatiblesSeleccionados
            );
        }


        // =====================================================
        // MODIFICAR EL OBJETO
        // =====================================================

        refaccionEditando.Nombre = nombre;

        refaccionEditando.Codigo = codigo;

        refaccionEditando.CategoriaId = categoria.Id;

        refaccionEditando.MarcaId = marca.Id;

        refaccionEditando.Precio = precio;

        refaccionEditando.Stock = stock;

        refaccionEditando.StockBajo =
            stock <= 5;

        refaccionEditando.EsUniversal =
            esUniversal;

        refaccionEditando.AutosCompatibles =
            autosSeleccionados;

        refaccionEditando.CategoriaNombre =
            categoria.Nombre;

        refaccionEditando.MarcaNombre =
            marca.Nombre;


        // =====================================================
        // ACTUALIZAR AUTOS PARA MOSTRAR EN LA TARJETA
        // =====================================================

        refaccionEditando.AutosDescripciones.Clear();

        if (!esUniversal)
        {
            foreach (int autoId in autosSeleccionados)
            {
                ModeloAuto? auto =
                    autos.FirstOrDefault(
                        a => a.Id == autoId
                    );

                if (auto != null)
                {
                    refaccionEditando
                        .AutosDescripciones
                        .Add(
                            auto.DescripcionCompleta
                        );
                }
            }
        }


        // =====================================================
        // AQUÍ VA LA LÍNEA QUE ME PREGUNTABAS
        // =====================================================

        await repoRefacciones.UpdateAsync(
            refaccionEditando
        );


        // =====================================================
        // ACTUALIZAR CONTADORES
        // =====================================================

        ActualizarTodo();


        // =====================================================
        // CERRAR FORMULARIO
        // =====================================================

        Formulario.Visibility =
            Visibility.Collapsed;

        modoFormulario =
            string.Empty;


        // =====================================================
        // GUARDAMOS EL NOMBRE ANTES DE LIMPIAR LA VARIABLE
        // =====================================================

        string nombreProducto =
            refaccionEditando.Nombre;

        refaccionEditando =
            null;


        // =====================================================
        // CONFIRMACIÓN
        // =====================================================

        await MostrarMensaje(
            "Producto actualizado",
            $"La refacción \"{nombreProducto}\" se actualizó correctamente."
        );
    }
}