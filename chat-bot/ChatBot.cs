#:package Robocode.TankRoyale.BotApi@0.34.1

using System;
using Robocode.TankRoyale.BotApi;
using Robocode.TankRoyale.BotApi.Events;
using Robocode.TankRoyale.BotApi.Graphics;

namespace ChatBot;

public class ChatBot : Bot
{
    static void Main(string[] args) => new ChatBot().Start();

    public override void Run()
    {
        BodyColor = Color.FromRgb(20, 140, 60);
        TurretColor = Color.FromRgb(15, 110, 50);
        RadarColor = Color.FromRgb(40, 190, 80);
        BulletColor = Color.FromRgb(90, 220, 120);
        ScanColor = Color.FromRgb(160, 255, 170);

        AdjustGunForBodyTurn = true;
        AdjustRadarForGunTurn = true;
        MaxSpeed = 6;

        while (IsRunning)
        {
            SetTurnRight(10_000);
            SetForward(8_000);
            SetTurnRadarRight(45);
            Go();
        }
    }

    public override void OnScannedBot(ScannedBotEvent e)
    {
        var gunBearing = GunBearingTo(e.X, e.Y);
        SetTurnGunLeft(gunBearing);

        var radarBearing = RadarBearingTo(e.X, e.Y);
        var radarOvershoot = Math.Sign(radarBearing) == 0 ? 1 : Math.Sign(radarBearing);
        SetTurnRadarLeft(radarBearing + radarOvershoot * 2);

        if (Math.Abs(gunBearing) <= 3 && GunHeat == 0)
        {
            var distance = DistanceTo(e.X, e.Y);
            var firePower = distance < 200 ? 3 : distance < 500 ? 2 : 1.2;
            Fire(Math.Min(firePower, Energy - 0.1));
        }

        if (gunBearing == 0)
        {
            Rescan();
        }
    }

    public override void OnHitBot(HitBotEvent e)
    {
        Fire(2.5);
        if (e.IsRammed)
        {
            SetTurnRight(15);
        }
    }

    public override void OnHitWall(HitWallEvent e)
    {
        SetBack(60);
        SetTurnRight(60);
    }
}
