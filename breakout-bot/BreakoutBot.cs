#:package Robocode.TankRoyale.BotApi@0.34.1

using Robocode.TankRoyale.BotApi;
using Robocode.TankRoyale.BotApi.Events;
using Robocode.TankRoyale.BotApi.Graphics;

namespace BreakoutBot;

public class BreakoutBot : Bot
{
    private double TargetHeading { get; set; } = 45;

    static void Main(string[] args) => new BreakoutBot().Start();

    public override void Run()
    {
        BodyColor = Color.FromRgb(230, 120, 30);
        TurretColor = Color.FromRgb(200, 90, 20);
        RadarColor = Color.FromRgb(255, 160, 60);
        BulletColor = Color.FromRgb(255, 200, 110);
        ScanColor = Color.FromRgb(255, 210, 140);

        AdjustGunForBodyTurn = true;
        AdjustRadarForGunTurn = true;
        MaxSpeed = Constants.MaxSpeed;

        while (IsRunning)
        {
            SteerTowardsTarget();
            TargetSpeed = Constants.MaxSpeed;
            SetForward(10_000);
            SetTurnRadarRight(40);
            Go();
        }
    }

    public override void OnHitWall(HitWallEvent e)
    {
        Bounce();
    }

    public override void OnHitBot(HitBotEvent e)
    {
        Bounce();
    }

    public override void OnScannedBot(ScannedBotEvent e)
    {
        var gunBearing = GunBearingTo(e.X, e.Y);
        SetTurnGunLeft(gunBearing);

        var radarBearing = RadarBearingTo(e.X, e.Y);
        SetTurnRadarLeft(radarBearing);

        if (Math.Abs(gunBearing) <= 3 && GunHeat == 0)
        {
            var distance = DistanceTo(e.X, e.Y);
            var power = distance < 150 ? 3 : distance < 400 ? 2 : 1;
            Fire(Math.Min(power, Energy - 0.1));
        }

        if (gunBearing == 0)
        {
            Rescan();
        }
    }

    private void SteerTowardsTarget()
    {
        var turn = NormalizeRelativeAngle(TargetHeading - Direction);
        SetTurnLeft(turn);
    }

    private void Bounce()
    {
        TargetHeading = NormalizeAbsolute(Direction + 90);
        SteerTowardsTarget();
        SetBack(20);
    }

    private static double NormalizeAbsolute(double angle)
    {
        angle %= 360;
        if (angle < 0) angle += 360;
        return angle;
    }
}
