#:package Robocode.TankRoyale.BotApi@0.34.1

using Robocode.TankRoyale.BotApi;
using Robocode.TankRoyale.BotApi.Events;
using Robocode.TankRoyale.BotApi.Graphics;

namespace ExampleBot;

public class ExampleBot : Bot
{
    static void Main(string[] args)
    {
        new ExampleBot().Start();
    }

    public override void Run()
    {
        BodyColor = Color.FromRgb(95, 184, 167);
        TurretColor = Color.FromRgb(255, 149, 0);
        RadarColor = Color.FromRgb(248, 90, 0);
        BulletColor = Color.FromRgb(255, 184, 0);
        ScanColor = Color.FromRgb(122, 204, 192);

        while (IsRunning)
        {
            Forward(100);
            TurnGunRight(360);
            Back(100);
            TurnGunRight(360);
        }
    }

    public override void OnScannedBot(ScannedBotEvent evt)
    {
        Fire(2.0);
    }

    public override void OnHitByBullet(HitByBulletEvent evt)
    {
        var bearing = CalcBearing(evt.Bullet.Direction);
        TurnRight(90 - bearing);
    }

    public override void OnHitWall(HitWallEvent evt)
    {
        Back(20);
    }
}
