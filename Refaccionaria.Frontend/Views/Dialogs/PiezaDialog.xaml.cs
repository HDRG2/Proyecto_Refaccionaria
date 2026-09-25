using System.Linq;
using Microsoft.UI.Xaml.Controls;
using Refaccionaria.Frontend.Models;
using Refaccionaria.Frontend.ViewModels;

namespace Refaccionaria.Frontend.Views.Dialogs;

public sealed partial class PiezaDialog : ContentDialog
{
    private MainPageViewModel? _viewModel;
    public MainPageViewModel? ViewModel
    {
        get => _viewModel;
        set
        {
            _viewModel = value;
            CargarCombos();
        }
    }

    private int? _editandoId;

    public PiezaDialog()
    {
        InitializeComponent();
        PrimaryButtonClick += PiezaDialog_PrimaryButtonClick;
    }

    private void CargarCombos()
    {
        if (_viewModel is null) return;
        CategoriaCombo.ItemsSource = _viewModel.CategoriasCatalogo;
        MarcaCombo.ItemsSource = _viewModel.MarcasCatalogo;
        AutosListView.ItemsSource = _viewModel.AutosCatalogo;
    }

    public void CargarDatos(Refaccion pieza)
    {
        _editandoId = pieza.Id;
        Title = "EDITAR PIEZA";
        PrimaryButtonText = "Guardar cambios";

        CodigoBox.Text = pieza.Codigo;
        NombreBox.Text = pieza.Nombre;
        CategoriaCombo.SelectedItem = _viewModel?.CategoriasCatalogo.FirstOrDefault(c => c.Id == pieza.CategoriaId);
        MarcaCombo.SelectedItem = _viewModel?.MarcasCatalogo.FirstOrDefault(m => m.Id == pieza.MarcaId);
        PrecioBox.Value = (double)pieza.Precio;
        StockBox.Value = pieza.Stock;

        AutosListView.SelectedItems.Clear();
        if (_viewModel is not null && pieza.AutosCompatibles is not null)
        {
            foreach (var autoId in pieza.AutosCompatibles)
            {
                var auto = _viewModel.AutosCatalogo.FirstOrDefault(a => a.Id == autoId);
                if (auto is not null) AutosListView.SelectedItems.Add(auto);
            }
        }
    }

    private async void PiezaDialog_PrimaryButtonClick(ContentDialog sender, ContentDialogButtonClickEventArgs args)
    {
        if (ViewModel is null) return;

        var categoriaSeleccionada = CategoriaCombo.SelectedItem as Categoria;
        var marcaSeleccionada = MarcaCombo.SelectedItem as Marca;
        var autosSeleccionados = AutosListView.SelectedItems.Cast<ModeloAuto>().Select(a => a.Id).ToList();

        var datos = new Refaccion
        {
            Codigo = CodigoBox.Text.Trim().ToUpperInvariant(),
            Nombre = NombreBox.Text.Trim(),
            CategoriaId = categoriaSeleccionada?.Id ?? 0,
            MarcaId = marcaSeleccionada?.Id ?? 0,
            Precio = (decimal)(double.IsNaN(PrecioBox.Value) ? 0 : PrecioBox.Value),
            Stock = (int)(double.IsNaN(StockBox.Value) ? 0 : StockBox.Value),
            AutosCompatibles = autosSeleccionados
        };

        var (exito, error) = await ViewModel.GuardarPiezaAsync(datos, _editandoId);
        if (!exito)
        {
            ErrorBar.Message = error ?? "Revisa los datos capturados.";
            ErrorBar.IsOpen = true;
            args.Cancel = true;
        }
    }
}