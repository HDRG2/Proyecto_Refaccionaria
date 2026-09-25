using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Refaccionaria.Frontend.ViewModels;
using Refaccionaria.Frontend.Views.Dialogs;


namespace Refaccionaria.Frontend.Views
{
    public sealed partial class MainPage : Page
    {
        public MainPageViewModel ViewModel { get; }
        private readonly string _nombreUsuario;

        public MainPage() : this("Usuario") { }

        public MainPage(string nombreUsuario)
        {
            _nombreUsuario = nombreUsuario;
            this.InitializeComponent();
            ViewModel = new MainPageViewModel();
            this.DataContext = ViewModel;
            this.Loaded += MainPage_Loaded;
        }

        private async void MainPage_Loaded(object sender, RoutedEventArgs e)
        {
            try
            {
                await ViewModel.InitializeAsync();
            }
            catch (Exception ex)
            {
                var dialog = new ContentDialog
                {
                    Title = "Error al cargar el administrador",
                    Content = ex.ToString(),
                    CloseButtonText = "Aceptar",
                    XamlRoot = this.XamlRoot
                };

                await dialog.ShowAsync();
            }
        }

        private void Buscar_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (sender is TextBox textBox)
                ViewModel.TextoBusqueda = textBox.Text;
        }

        private void OrdenCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (sender is ComboBox combo && combo.SelectedItem is ComboBoxItem selectedItem && selectedItem.Tag is string tag)
            {
                ViewModel.Orden = tag;
            }
        }

        private async void NuevaPieza_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new PiezaDialog { XamlRoot = this.XamlRoot, ViewModel = ViewModel };
            await dialog.ShowAsync();
        }
    }
}