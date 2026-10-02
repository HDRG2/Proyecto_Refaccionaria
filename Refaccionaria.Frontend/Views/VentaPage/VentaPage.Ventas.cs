using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media.Animation;

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Frontend.Models;
using Refaccionaria.Backend.Repositories;

namespace Refaccionaria.Frontend.Views
{
    public sealed partial class VentaPage : Page
    {
        // =========================================================
        // CONFIRMAR VENTA
        // =========================================================

        private async void Confirmar_Click(
            object sender,
            RoutedEventArgs e)
        {
            // =====================================================
            // 1. VALIDAR QUE HAYA PRODUCTOS
            // =====================================================

            if (_ticket.Count == 0)
            {
                return;
            }

            BtnConfirmar.IsEnabled = false;

            try
            {
                // =================================================
                // 2. LEER EL PAGO
                // =================================================

                decimal recibido;

                if (_metodoPago == "Efectivo")
                {
                    if (!IntentarLeerDecimal(
                            TxtRecibido.Text,
                            out recibido))
                    {
                        await MostrarMensaje(
                            "Cantidad inválida",
                            "Ingresa la cantidad recibida."
                        );

                        BtnConfirmar.IsEnabled = true;

                        return;
                    }
                }
                else
                {
                    recibido = _total;
                }


                // =================================================
                // 3. REGISTRAR LA VENTA
                // =================================================

                Venta venta =
                    await ventaService.RegistrarVentaAsync(
                        _usuarioActual,
                        _ticket,
                        _metodoPago,
                        recibido
                    );


                // =================================================
                // 4. ACTUALIZAR INVENTARIO LOCAL
                // =================================================

                await repoRefacciones.ReloadAsync();

                _refacciones =
                    (await repoRefacciones.GetAllAsync())
                    .ToList();

                foreach (Refaccion refaccion in _refacciones)
                {
                    CompletarDatosRefaccion(refaccion);
                }


                // =================================================
                // 5. MOSTRAR VENTA EXITOSA
                // =================================================

                TxtFolio.Text =
                    venta.Folio;

                TxtMetodoExito.Text =
                    venta.MetodoPago;

                TxtCambioExito.Text =
                    venta.Cambio.ToString("C");

                TxtDetalleExito.Text =
                    $"Venta por {venta.Total:C} registrada correctamente.";

                PanelCobro.Visibility =
                    Visibility.Collapsed;

                PanelExito.Visibility =
                    Visibility.Visible;


                // =================================================
                // 6. VACIAR CARRITO
                // =================================================

                _ticket.Clear();

                ActualizarTotales();


                // =================================================
                // 7. ACTUALIZAR CATÁLOGO
                // =================================================

                AplicarFiltros();
            }
            catch (Exception ex)
            {
                BtnConfirmar.IsEnabled = true;


                await MostrarMensaje(
                    "No se pudo registrar la venta",
                    ex.Message
                );


                // =================================================
                // Volver a cargar inventario por seguridad
                // =================================================

                try
                {
                    await repoRefacciones.ReloadAsync();

                    _refacciones =
                        (await repoRefacciones.GetAllAsync())
                        .ToList();

                    foreach (Refaccion refaccion in _refacciones)
                    {
                        CompletarDatosRefaccion(refaccion);
                    }

                    AplicarFiltros();
                }
                catch
                {
                    await MostrarMensaje(
                        "Error crítico",
                        "No fue posible volver a cargar el inventario.\n\n" +
                        "No continúes realizando ventas y contacta al administrador."
                    );

                    Application.Current.Exit();
                }
            }
        }
        
        // =========================================================
        // CANCELAR COBRO
        // =========================================================

        private void CancelarCobro_Click(
            object sender,
            RoutedEventArgs e)
        {
            CapaCobro.Visibility =
                Visibility.Collapsed;


            PanelCobro.Visibility =
                Visibility.Visible;


            PanelExito.Visibility =
                Visibility.Collapsed;


            BtnConfirmar.IsEnabled =
                false;
        }


        // =========================================================
        // CERRAR VENTA EXITOSA
        // =========================================================

        private void CerrarExito_Click(
            object sender,
            RoutedEventArgs e)
        {
            CapaCobro.Visibility =
                Visibility.Collapsed;


            PanelCobro.Visibility =
                Visibility.Visible;


            PanelExito.Visibility =
                Visibility.Collapsed;


            CerrarTicket();


            TxtBuscar.Focus(
                FocusState.Programmatic
            );
        }
    }
}