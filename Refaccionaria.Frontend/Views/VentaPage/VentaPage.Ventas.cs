using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media.Animation;

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading.Tasks;

using Refaccionaria.Frontend.Models;

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
            if (_ticket.Count == 0)
            {
                return;
            }


            BtnConfirmar.IsEnabled =
                false;


            try
            {
                // -------------------------------------------------
                // 1. VALIDAR EXISTENCIAS OTRA VEZ
                // -------------------------------------------------

                foreach (DetalleVenta linea in _ticket)
                {
                    Refaccion? refaccion =
                        _refacciones.FirstOrDefault(
                            r =>
                                r.Id ==
                                linea.RefaccionId
                        );


                    if (refaccion == null)
                    {
                        await MostrarMensaje(
                            "Producto no encontrado",
                            "Uno de los productos del ticket ya no existe."
                        );


                        BtnConfirmar.IsEnabled =
                            true;


                        return;
                    }


                    if (!refaccion.Activo)
                    {
                        await MostrarMensaje(
                            "Producto retirado",
                            $"\"{refaccion.Nombre}\" ya no está disponible."
                        );


                        BtnConfirmar.IsEnabled =
                            true;


                        return;
                    }


                    if (refaccion.Stock <
                        linea.Cantidad)
                    {
                        await MostrarMensaje(
                            "Existencia insuficiente",
                            $"\"{refaccion.Nombre}\" solo tiene {refaccion.Stock} unidades disponibles."
                        );


                        BtnConfirmar.IsEnabled =
                            true;


                        return;
                    }
                }


                // -------------------------------------------------
                // 2. DATOS DEL PAGO
                // -------------------------------------------------

                decimal recibido;
                decimal cambio;


                if (_metodoPago ==
                    "Efectivo")
                {
                    if (!IntentarLeerDecimal(
                            TxtRecibido.Text,
                            out recibido))
                    {
                        await MostrarMensaje(
                            "Cantidad inválida",
                            "Ingresa la cantidad recibida."
                        );


                        BtnConfirmar.IsEnabled =
                            true;


                        return;
                    }


                    if (recibido <
                        _total)
                    {
                        await MostrarMensaje(
                            "Pago insuficiente",
                            "La cantidad recibida es menor al total de la venta."
                        );


                        BtnConfirmar.IsEnabled =
                            true;


                        return;
                    }


                    cambio =
                        recibido - _total;
                }
                else
                {
                    recibido =
                        _total;

                    cambio =
                        0m;
                }


                // -------------------------------------------------
                // 3. CREAR VENTA
                // -------------------------------------------------

                Venta venta =
                    new()
                    {
                        Folio =
                            GenerarFolio(),

                        Fecha =
                            DateTime.Now,

                        /*
                         * Actualmente VentaPage no recibe todavía
                         * el Usuario completo, por lo que dejamos
                         * UsuarioId en 0.
                         *
                         * Después podemos pasar el vendedor que
                         * inició sesión y guardar su Id real.
                         */

                        UsuarioId =
                            0,

                        MetodoPago =
                            _metodoPago,

                        Referencia =
                            string.Empty,

                        Recibido =
                            recibido,

                        Cambio =
                            cambio,

                        Total =
                            _total
                    };


                // -------------------------------------------------
                // 4. GUARDAR CABECERA DE LA VENTA
                // -------------------------------------------------

                await repoVentas.AddAsync(
                    venta
                );


                // -------------------------------------------------
                // 5. GUARDAR DETALLES
                // -------------------------------------------------

                foreach (DetalleVenta lineaTicket in _ticket)
                {
                    DetalleVenta detalle =
                        new()
                        {
                            VentaId =
                                venta.Id,

                            RefaccionId =
                                lineaTicket.RefaccionId,

                            Cantidad =
                                lineaTicket.Cantidad,

                            PrecioUnitario =
                                lineaTicket.PrecioUnitario,

                            Refaccion =
                                lineaTicket.Refaccion
                        };

                    await repoDetalleVentas.AddAsync(
                        detalle
                    );

                    venta.Lineas.Add(
                        detalle
                    );
                }

                // MUY IMPORTANTE:
                // Actualizamos la venta después de agregar sus líneas.
                await repoVentas.UpdateAsync(
                    venta
                );


                // -------------------------------------------------
                // 6. DESCONTAR EXISTENCIAS
                // -------------------------------------------------

                foreach (DetalleVenta linea in _ticket)
                {
                    Refaccion? refaccion =
                        _refacciones.FirstOrDefault(
                            r =>
                                r.Id ==
                                linea.RefaccionId
                        );

                    if (refaccion == null)
                    {
                        continue;
                    }

                    refaccion.Stock -= linea.Cantidad;

                    if (refaccion.Stock <= 0)
                    {
                        refaccion.Stock = 0;
                        refaccion.StockBajo = true;

                        // Al quedarse sin existencia, se retira del inventario activo.
                        refaccion.Activo = false;
                    }
                    else
                    {
                        refaccion.StockBajo = refaccion.Stock <= 5;
                        refaccion.Activo = true;
                    }

                    await repoRefacciones.UpdateAsync(refaccion);
                }


                // -------------------------------------------------
                // 7. MOSTRAR ÉXITO
                // -------------------------------------------------

                TxtFolio.Text =
                    venta.Folio;


                TxtMetodoExito.Text =
                    venta.MetodoPago;


                TxtCambioExito.Text =
                    cambio.ToString("C");


                TxtDetalleExito.Text =
                    $"Venta por {_total:C} registrada correctamente.";


                PanelCobro.Visibility =
                    Visibility.Collapsed;


                PanelExito.Visibility =
                    Visibility.Visible;


                // -------------------------------------------------
                // 8. VACIAR CARRITO
                // -------------------------------------------------

                _ticket.Clear();

                ActualizarTotales();


                // -------------------------------------------------
                // 9. REFRESCAR CATÁLOGO
                // -------------------------------------------------


            AplicarFiltros();

            }
            catch (Exception ex)
            {
                BtnConfirmar.IsEnabled =
                    true;


                await MostrarMensaje(
                    "Error al registrar la venta",
                    ex.Message
                );
            }
        }


        // =========================================================
        // GENERAR FOLIO
        // =========================================================

        private static string GenerarFolio()
        {
            return
                $"V-{DateTime.Now:yyyyMMdd-HHmmssfff}";
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