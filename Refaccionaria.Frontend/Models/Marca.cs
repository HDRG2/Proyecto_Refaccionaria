using CommunityToolkit.Mvvm.ComponentModel;
using Refaccionaria.Backend.Repositories;

namespace Refaccionaria.Frontend.Models;

public partial class Marca : ObservableObject, IEntity
{
    [ObservableProperty]
    private int id;

    [ObservableProperty]
    private string nombre = string.Empty;
}
