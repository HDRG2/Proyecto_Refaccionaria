using Microsoft.UI.Text;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media.Animation;

using System;
using System.Collections.Generic;
using System.Linq;

using Windows.Foundation;

using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;

namespace Refaccionaria.Frontend.Views
{
    // =========================================================
    // BOTONES DE CATEGORÍA
    // =========================================================
    public sealed partial class VentaPage
    {
        private const double EspacioEntreBotones = 8;

        // Relleno interno de la píldora (izquierda + derecha) más un margen.
        private const double RellenoBoton = 44;

        private readonly List<RadioButton> _botonesCategoria = new();

        private int _columnasActuales;


        private void LlenarCategorias()
        {
            // Botones anteriores (si se recargan los datos).
            foreach (RadioButton boton in _botonesCategoria.Where(b => b != RbTodos))
            {
                boton.Checked -= Tipo_Checked;
            }

            _botonesCategoria.Clear();
            _botonesCategoria.Add(RbTodos);


            // Mismo orden en que se registraron, sin repetidos.
            List<string> nombres =
                _categorias
                    .OrderBy(c => c.Id)
                    .Select(c => c.Nombre?.Trim() ?? string.Empty)
                    .Where(n => n.Length > 0)
                    .Distinct(StringComparer.OrdinalIgnoreCase)
                    .ToList();


            bool seleccionSigueExistiendo = false;

            foreach (string nombre in nombres)
            {
                RadioButton pildora = new()
                {
                    Content = nombre,
                    Tag = nombre,
                    GroupName = "Tipo",
                    Style = RbTodos.Style,
                    HorizontalAlignment = HorizontalAlignment.Stretch,
                };

                ToolTipService.SetToolTip(pildora, nombre);

                if (string.Equals(
                        nombre,
                        _tipoSeleccionado,
                        StringComparison.OrdinalIgnoreCase))
                {
                    pildora.IsChecked = true;
                    seleccionSigueExistiendo = true;
                }

                pildora.Checked += Tipo_Checked;

                _botonesCategoria.Add(pildora);
            }


            // Si la categoría elegida ya no existe, regresa a "Todos".
            if (!seleccionSigueExistiendo)
            {
                _tipoSeleccionado = "Todos";
                RbTodos.IsChecked = true;
            }

            _columnasActuales = 0;
            AcomodarCategorias();
        }


        private void PanelCategorias_SizeChanged(
            object sender,
            SizeChangedEventArgs e)
        {
            if (Math.Abs(e.NewSize.Width - e.PreviousSize.Width) > 0.5)
            {
                AcomodarCategorias();
            }
        }


        // ---------------------------------------------------------
        // Reparte los botones en filas parejas.
        // ---------------------------------------------------------
        private void AcomodarCategorias()
        {
            double ancho = PanelCategorias.ActualWidth;

            if (ancho <= 0 || _botonesCategoria.Count == 0)
            {
                return;
            }

            int total = _botonesCategoria.Count;

            // Cuántos caben por fila sin cortar el nombre más largo.
            double anchoMinimo =
                _botonesCategoria.Max(b => AnchoTexto(b.Content?.ToString())) + RellenoBoton;

            int maximoPorFila = Math.Max(
                1,
                (int)((ancho + EspacioEntreBotones) / (anchoMinimo + EspacioEntreBotones))
            );

            // Mismo número de filas, pero repartidas parejo:
            // 17 con máximo 12 por fila -> 2 filas -> 9 + 8.
            int filas = (total + maximoPorFila - 1) / maximoPorFila;
            int porFila = (total + filas - 1) / filas;

            if (porFila == _columnasActuales && PanelCategorias.Children.Count == filas)
            {
                return; 
            }

            _columnasActuales = porFila;


            // Saca los botones de sus filas anteriores.
            foreach (RadioButton boton in _botonesCategoria)
            {
                if (boton.Parent is Panel padre)
                {
                    padre.Children.Remove(boton);
                }
            }

            PanelCategorias.Children.Clear();


            // Filas: las primeras llevan un botón más si no sale exacto.
            int indice = 0;
            int filasConUnoMas = total - (porFila - 1) * filas;

            for (int fila = 0; fila < filas; fila++)
            {
                int enEstaFila = fila < filasConUnoMas ? porFila : porFila - 1;

                Grid renglon = new()
                {
                    ColumnSpacing = EspacioEntreBotones,
                };

                for (int columna = 0; columna < enEstaFila; columna++)
                {
                    renglon.ColumnDefinitions.Add(
                        new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) }
                    );

                    RadioButton boton = _botonesCategoria[indice++];
                    Grid.SetColumn(boton, columna);
                    renglon.Children.Add(boton);
                }

                PanelCategorias.Children.Add(renglon);
            }
        }


        private static double AnchoTexto(string? texto)
        {
            TextBlock medida = new()
            {
                Text = texto ?? string.Empty,
                FontSize = 13,
                FontWeight = FontWeights.SemiBold,
            };

            medida.Measure(new Size(double.PositiveInfinity, double.PositiveInfinity));
            return medida.DesiredSize.Width;
        }


        // =========================================================
        // FLECHA: ESCONDER / MOSTRAR CATEGORÍAS
        // =========================================================

        private bool _categoriasVisibles = true;

        private void MostrarCategorias_Click(
            object sender,
            RoutedEventArgs e)
        {
            _categoriasVisibles = !_categoriasVisibles;

            TimeSpan duracion = TimeSpan.FromMilliseconds(200);

            // Gira la flecha: arriba (0°) = visibles, abajo (180°) = escondidas.
            DoubleAnimation giro = new()
            {
                To = _categoriasVisibles ? 0 : 180,
                Duration = duracion,
                EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseOut },
            };
            Storyboard.SetTarget(giro, GiroFlecha);
            Storyboard.SetTargetProperty(giro, "Angle");

            // Desvanece los botones.
            DoubleAnimation opacidad = new()
            {
                To = _categoriasVisibles ? 1 : 0,
                Duration = duracion,
            };
            Storyboard.SetTarget(opacidad, PanelCategorias);
            Storyboard.SetTargetProperty(opacidad, "Opacity");

            Storyboard animacion = new();
            animacion.Children.Add(giro);
            animacion.Children.Add(opacidad);

            if (_categoriasVisibles)
            {
                PanelCategorias.Visibility = Visibility.Visible;
            }
            else
            {
                animacion.Completed += (_, _) =>
                {
                    if (!_categoriasVisibles)
                    {
                        PanelCategorias.Visibility = Visibility.Collapsed;
                    }
                };
            }

            animacion.Begin();

            ToolTipService.SetToolTip(
                BtnMostrarCategorias,
                _categoriasVisibles ? "Ocultar categorías" : "Mostrar categorías"
            );
        }
    }
}


