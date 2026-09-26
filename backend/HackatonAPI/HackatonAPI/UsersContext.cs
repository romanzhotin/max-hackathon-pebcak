using Microsoft.EntityFrameworkCore;
using HackatonAPI.Models;
using System.Diagnostics;

namespace HackatonAPI
{
    public class UsersContext : DbContext
    {
        public DbSet<User> Users { get; set; }

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {

            optionsBuilder.LogTo(Console.WriteLine);

            if (Debugger.IsAttached)
            {
                DotNetEnv.Env.TraversePath().Load();
            }

            string connString = Environment.GetEnvironmentVariable("CONN_STRING") ?? throw new ArgumentException("Variable CONN_STRING is not found");

            optionsBuilder.UseNpgsql(connString);
        }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<User>().ToTable("users");
        }

        //private Exception CreateException(string variableName)
        //{
        //    return new ArgumentException($"Variable {variableName} is not found");
        //}
    }
}
