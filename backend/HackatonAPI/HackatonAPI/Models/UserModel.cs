namespace HackatonAPI.Models
{
    public class User
    {
        public int Id { get; set; }
        public long? MaxId { get; set; }
        public string? City { get; set; }
        public List<string>? Categories { get; set; }
    }
}
