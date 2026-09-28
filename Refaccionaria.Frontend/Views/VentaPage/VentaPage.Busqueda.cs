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
        private const string TODOS_ANIOS = "Cualquier año";
        // =========================================================
        // LLENAR MARCAS
        // =========================================================

        private void LlenarMarcas()
        {
            if (CmbMarca == null)
            {
                return;
            }

            string? seleccionAnterior =
                CmbMarca.SelectedItem?.ToString();

            CmbMarca.Items.Clear();

            CmbMarca.Items.Add(
                TODAS_MARCAS
            );

            IEnumerable<string> nombres =
                _marcas
                .Select(m => m.Nombre)
                .Where(n =>
                    !string.IsNullOrWhiteSpace(n))
                .Distinct(
                    StringComparer.OrdinalIgnoreCase
                )
                .OrderBy(n => n);

            foreach (string nombre in nombres)
            {
                CmbMarca.Items.Add(
                    nombre
                );
            }

            if (!string.IsNullOrWhiteSpace(
                    seleccionAnterior))
            {
                for (int i = 0;
                     i < CmbMarca.Items.Count;
                     i++)
                {
                    if (string.Equals(
                            CmbMarca.Items[i]?.ToString(),
                            seleccionAnterior,
                            StringComparison.OrdinalIgnoreCase))
                    {
                        CmbMarca.SelectedIndex = i;
                        return;
                    }
                }
            }

            CmbMarca.SelectedIndex = 0;
        }


        // =========================================================
        // LLENAR MODELOS
        // =========================================================

        private void LlenarModelos()
        {
            if (CmbMarca == null ||
                CmbModelo == null)
            {
                return;
            }

            CmbModelo.Items.Clear();

            CmbModelo.Items.Add(
                TODOS_MODELOS
            );

            string marcaSeleccionada =
                CmbMarca.SelectedItem?.ToString()
                ?? TODAS_MARCAS;

            IEnumerable<string> modelos;

            if (marcaSeleccionada ==
                TODAS_MARCAS)
            {
                modelos =
                    _autos
                    .Select(a => a.Modelo);
            }
            else
            {
                modelos =
                    _autos
                    .Where(a =>
                        string.Equals(
                            a.Marca,
                            marcaSeleccionada,
                            StringComparison.OrdinalIgnoreCase
                        ))
                    .Select(a => a.Modelo);
            }

            foreach (string modelo in
                     modelos
                     .Where(m =>
                         !string.IsNullOrWhiteSpace(m))
                     .Distinct(
                         StringComparer.OrdinalIgnoreCase
                     )
                     .OrderBy(m => m))
            {
                CmbModelo.Items.Add(
                    modelo
                );
            }

            CmbModelo.SelectedIndex = 0;
        }

        // =========================================================
        // LLENAR AÑOS
        // =========================================================

        private void LlenarAnios()
        {
            if (CmbMarca == null ||
                CmbModelo == null ||
                CmbAnio == null)
            {
                return;
            }

            CmbAnio.Items.Clear();
            CmbAnio.Items.Add(TODOS_ANIOS);

            string marcaSeleccionada =
                CmbMarca.SelectedItem?.ToString()
                ?? TODAS_MARCAS;

            string modeloSeleccionado =
                CmbModelo.SelectedItem?.ToString()
                ?? TODOS_MODELOS;

            IEnumerable<ModeloAuto> vehiculos = _autos;

            // Filtrar por marca
            if (marcaSeleccionada != TODAS_MARCAS)
            {
                vehiculos = vehiculos.Where(a =>
                    string.Equals(
                        a.Marca,
                        marcaSeleccionada,
                        StringComparison.OrdinalIgnoreCase
                    )
                );
            }

            // Filtrar por modelo
            if (modeloSeleccionado != TODOS_MODELOS)
            {
                vehiculos = vehiculos.Where(a =>
                    string.Equals(
                        a.Modelo,
                        modeloSeleccionado,
                        StringComparison.OrdinalIgnoreCase
                    )
                );
            }

            IEnumerable<int> anios =
                vehiculos
                .SelectMany(a =>
                    Enumerable.Range(
                        a.AnioInicio,
                        a.AnioFin - a.AnioInicio + 1
                    )
                )
                .Distinct()
                .OrderByDescending(a => a);

            foreach (int anio in anios)
            {
                CmbAnio.Items.Add(anio);
            }

            CmbAnio.SelectedIndex = 0;
        }


        // =========================================================
        // FILTRAR PRODUCTOS
        // =========================================================

        private void AplicarFiltros()
        {
            if (!_listo)
            {
                return;
            }


            IEnumerable<Refaccion> lista =
                _refacciones.Where(
                    r =>
                        r.Activo &&
                        r.Stock > 0
                );


            // -----------------------------------------------------
            // BÚSQUEDA
            // -----------------------------------------------------

            string texto =
                TxtBuscar.Text?
                    .Trim()
                    .ToLowerInvariant()
                ?? string.Empty;


            if (!string.IsNullOrWhiteSpace(
                    texto))
            {
                lista =
                    lista.Where(
                        r =>
                            Contiene(
                                r.Nombre,
                                texto
                            ) ||

                            Contiene(
                                r.Codigo,
                                texto
                            ) ||

                            Contiene(
                                r.MarcaNombre,
                                texto
                            ) ||

                            Contiene(
                                r.CategoriaNombre,
                                texto
                            ) ||

                            r.AutosDescripciones.Any(
                                a => Contiene(
                                    a,
                                    texto
                                )
                            )
                    );
            }

            // -----------------------------------------------------
            // CATEGORÍA
            // -----------------------------------------------------

            if (!string.Equals(
                    _tipoSeleccionado,
                    "Todos",
                    StringComparison.OrdinalIgnoreCase))
            {
                lista =
                    lista.Where(
                        r =>
                            string.Equals(
                                r.CategoriaNombre,
                                _tipoSeleccionado,
                                StringComparison.OrdinalIgnoreCase
                            )
                    );
            }


            // -----------------------------------------------------
            // MARCA
            // -----------------------------------------------------

            string marca =
                CmbMarca.SelectedItem?.ToString()
                ?? TODAS_MARCAS;


            if (marca != TODAS_MARCAS)
            {
                /*
                 * Primero comprobamos la marca de la refacción.
                 * También permitimos encontrar productos por
                 * compatibilidad con autos de esa marca.
                 */

                HashSet<int> autosMarca =
                    _autos
                    .Where(
                        a => string.Equals(
                            a.Marca,
                            marca,
                            StringComparison.OrdinalIgnoreCase
                        ))
                    .Select(a => a.Id)
                    .ToHashSet();


                lista =
                    lista.Where(
                        r =>
                            string.Equals(
                                r.MarcaNombre,
                                marca,
                                StringComparison.OrdinalIgnoreCase
                            ) ||

                            r.EsUniversal ||

                            (
                                r.AutosCompatibles != null &&
                                r.AutosCompatibles.Any(
                                    id =>
                                        autosMarca.Contains(id)
                                )
                            )
                    );
            }


            // -----------------------------------------------------
            // MODELO
            // -----------------------------------------------------

            string modelo =
                CmbModelo.SelectedItem?.ToString()
                ?? TODOS_MODELOS;


            if (modelo != TODOS_MODELOS)
            {
                HashSet<int> autosModelo =
                    _autos
                    .Where(
                        a => string.Equals(
                            a.Modelo,
                            modelo,
                            StringComparison.OrdinalIgnoreCase
                        ))
                    .Select(a => a.Id)
                    .ToHashSet();


                lista =
                    lista.Where(
                        r =>
                            r.EsUniversal ||

                            (
                                r.AutosCompatibles != null &&
                                r.AutosCompatibles.Any(
                                    id =>
                                        autosModelo.Contains(id)
                                )
                            )
                    );
            }


            // -----------------------------------------------------
            // ORDEN
            // -----------------------------------------------------

            int orden =
                CmbOrden.SelectedIndex;


            lista =
                orden switch
                {
                    1 => lista
                        .OrderBy(r => r.Precio),

                    2 => lista
                        .OrderByDescending(
                            r => r.Precio
                        ),

                    3 => lista
                        .OrderByDescending(
                            r => r.Stock
                        ),

                    _ => lista
                        .OrderBy(r => r.Nombre)
                };


            // -----------------------------------------------------
            // ACTUALIZAR INTERFAZ
            // -----------------------------------------------------

            _resultados.Clear();


            foreach (Refaccion refaccion in lista)
            {
                _resultados.Add(
                    refaccion
                );
            }


            TxtSinResultados.Visibility =
                _resultados.Count == 0
                    ? Visibility.Visible
                    : Visibility.Collapsed;
        }


        private static bool Contiene(
            string? origen,
            string texto)
        {
            if (string.IsNullOrWhiteSpace(
                    origen))
            {
                return false;
            }


            return origen
                .ToLowerInvariant()
                .Contains(texto);
        }


        // =========================================================
        // EVENTOS DE FILTROS
        // =========================================================

        private void Buscar_TextChanged(
            object sender,
            TextChangedEventArgs e)
        {
            AplicarFiltros();
        }
        private void Modelo_Changed(
        object sender,
        SelectionChangedEventArgs e)
        {
            if (!_listo)
            {
                return;
            }

            _listo = false;

            LlenarAnios();

            _listo = true;

            AplicarFiltros();
        }

        private void Filtro_Changed(
    object sender,
    SelectionChangedEventArgs e)
        {
            if (!_listo)
            {
                return;
            }

            AplicarFiltros();
        }


        private void Marca_Changed(
            object sender,
            SelectionChangedEventArgs e)
        {
            if (!_listo)
            {
                return;
            }


            _listo = false;

            LlenarModelos();
            LlenarAnios();

            _listo = true;

            AplicarFiltros();
        }


        private void Tipo_Checked(
            object sender,
            RoutedEventArgs e)
        {
            if (sender is not RadioButton pildora)
            {
                return;
            }


            _tipoSeleccionado =
                pildora.Tag?.ToString()
                ?? "Todos";


            AplicarFiltros();
        }


        private void QuitarFiltros_Click(
            object sender,
            RoutedEventArgs e)
        {
            _listo = false;


            TxtBuscar.Text =
                string.Empty;

            CmbMarca.SelectedIndex =
                0;

            LlenarModelos();

            CmbModelo.SelectedIndex =
                0;

            CmbOrden.SelectedIndex =
                0;

            RbTodos.IsChecked =
                true;

            _listo = true;

            AplicarFiltros();
        }
    }
}