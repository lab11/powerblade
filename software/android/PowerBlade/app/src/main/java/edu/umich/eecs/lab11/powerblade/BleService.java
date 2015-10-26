package edu.umich.eecs.lab11.powerblade;

import android.app.Service;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Handler;
import android.os.IBinder;
import android.preference.PreferenceManager;
import android.util.Log;
import android.widget.Toast;

import java.nio.ByteBuffer;
import java.text.DecimalFormat;
import java.util.Arrays;

public class BleService extends Service {

    private boolean paused;
    private boolean mScanning;
    private Intent thisIntent;
    private Handler mScanHandler;
    private Integer radioSilenceCount = 0;
    private SharedPreferences cur_settings;
    private BluetoothManager mBluetoothManager;
    private BluetoothAdapter mBluetoothAdapter;
    private DecimalFormat di = new DecimalFormat("0");
    private DecimalFormat df = new DecimalFormat("0.##");

    // Pauses scanning after SCAN_PERIOD milliseconds, restarts 1 second later
    private final Integer SCAN_PERIOD = 10000;

    @Override
    public void onCreate() {
        super.onCreate();
        mScanHandler = new Handler();
        cur_settings = PreferenceManager.getDefaultSharedPreferences(this);
        if (!getPackageManager().hasSystemFeature(PackageManager.FEATURE_BLUETOOTH_LE)) {
            Toast.makeText(this, "BLE not supported", Toast.LENGTH_SHORT).show();
            stopSelf();
        }
        mBluetoothManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
        mBluetoothAdapter = mBluetoothManager.getAdapter();
        if (mBluetoothAdapter == null) {
            Toast.makeText(this, "Bluetooth not supported", Toast.LENGTH_SHORT).show();
            stopSelf();
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (!mBluetoothAdapter.isEnabled()) {
            try {
                mBluetoothAdapter.enable();
            } catch (Exception e) {
                Intent enableBtIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
                enableBtIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                getBaseContext().startActivity(enableBtIntent);
            }
        }
        paused = false;
        thisIntent = intent;
        scanLeDevice(true); // Start BLE Scan
        return super.onStartCommand(intent, flags, startId);
    }

    @Override
    public void onDestroy() {
        paused = true;
        mScanning = false;
        mBluetoothAdapter.stopLeScan(mLeScanCallback); // Stop BLE Scan
        super.onDestroy();
    }

    private void scanLeDevice(final boolean enable) {
        if (enable & !paused & !mScanning) {
            mScanHandler.postDelayed(new Runnable() { @Override public void run() { scanLeDevice(false); } }, SCAN_PERIOD);
            try { mScanning = mBluetoothAdapter.startLeScan(mLeScanCallback); } catch (Exception e) { e.printStackTrace(); }
        } else {
            if (!paused) {
                if (radioSilenceCount++ > 5) { // No devices detected for 1 min, restart service to be safe
                    mScanHandler.postDelayed(new Runnable() {
                        @Override
                        public void run() {
                            startService(thisIntent);
                            scanLeDevice(true);
                        }
                    }, 5000);
                    System.out.println("PERIPHERALS ARE NOT BEING SCANNED. RESTARTING SERVICE.");
                    mBluetoothAdapter.disable();
                    stopSelf();
                } else mScanHandler.postDelayed(new Runnable() { @Override public void run() { scanLeDevice(true); } }, 1000);
            }
            try {
                mBluetoothAdapter.stopLeScan(mLeScanCallback);
                mScanning = false;
            } catch (Exception e) { e.printStackTrace(); }

        }
    }

    private BluetoothAdapter.LeScanCallback mLeScanCallback = new BluetoothAdapter.LeScanCallback() {
        @Override
        public void onLeScan(final BluetoothDevice device, final int rssi, final byte[] scanRecord) {
            try {
                radioSilenceCount=0;
                //System.out.println(device.getName() + " : " + getHexString(scanRecord));
                parseStuff(device, rssi, scanRecord);
            } catch (Exception e) { e.printStackTrace(); }
        }
    };

    @Override
    public IBinder onBind(Intent intent) { return null; }

    public void parseStuff(BluetoothDevice device, int rssi, byte[] scanRecord) {

        // This is a PowerBlade if:
        //  packet is long enough
        //  initial junk is correct
        //  manufacturer data is the next field
        //  company ID is 0x4908
        if (scanRecord.length > 7 &&
                scanRecord[0] == (byte)0x02 && scanRecord[1] == (byte)0x01 && scanRecord[2] == (byte)0x06 &&
                scanRecord[4] == (byte)0xFF &&
                scanRecord[5] == (byte)0x08 && scanRecord[6] == (byte)0x49) {
            Log.d("NOTE", "Found a PowerBlade!");

            // check length of packet
            int data_len = scanRecord[3] - 3;
            if (data_len + 7 > scanRecord.length) {
                Log.e("ERROR", "Bad scanRecord");
                return;
            }

            // default values
            double pbid = 0;
            double vrms = 0;
            double reap = 0;
            double appp = 0;
            double wthr = 0;
            double pwfr = 0;

            // get advertisement data
            byte[] data = Arrays.copyOfRange(scanRecord, 7, 7 + data_len);
            byte powerblade_version = data[0];
            pbid = (double)powerblade_version;
            switch (powerblade_version) {

                case (byte)0x01:
                    Log.d("NOTE", "PowerBlade version 1");

//                    // print advertisement to console. Good for debugging
//                    String advdata = "adv data: [";
//                    for (int i=0; i<scanRecord.length; i++) {
//                        advdata += String.format("%02X", scanRecord[i]);
//                        advdata += " ";
//                    }
//                    advdata += "]";
//                    System.out.println(advdata);

                    // get data values
                    int sequence_num = ByteBuffer.wrap(data,  1, 4).getInt();
                    int pscale = ByteBuffer.wrap(data,  5, 2).getShort();
                    double vscale = (double)data[7];
                    int whscale = (int)data[8];
                    double v_rms = (double)data[9];
                    double real_power = (double)ByteBuffer.wrap(data, 10, 2).getShort();
                    double apparent_power = (double)ByteBuffer.wrap(data, 12, 2).getShort();
                    int watt_hours = ByteBuffer.wrap(data, 14, 4).getInt();
                    byte flags = data[18];

                    // apply math
                    double volt_scale = vscale/50;
                    double power_scale = (pscale & 0x0FFF) * Math.pow(10.0, -1.0*((pscale & 0xF000) >> 12));
                    int wh_shift = whscale;
                    vrms = v_rms*volt_scale;
                    reap = real_power*power_scale;
                    appp = apparent_power*power_scale;
                    if (volt_scale > 0) {
                        wthr = (watt_hours << wh_shift)*(power_scale/3600.0);
                    } else {
                        wthr = (double)watt_hours;
                    }
                    pwfr = reap/appp;

                    break;

                default:
                    Log.d("NOTE", "Can't handle PowerBlade version " + String.valueOf(powerblade_version));
                    break;
            }

            // Set magic string values that somehow update the GUI
            cur_settings.edit().putString("address",      device.getAddress()).apply();
            cur_settings.edit().putString("id",             di.format( pbid )).apply();
            cur_settings.edit().putString("power",          di.format( reap )).apply();
            cur_settings.edit().putString("v_rms",          df.format( vrms )).apply();
            cur_settings.edit().putString("true_power",     df.format( reap )).apply();
            cur_settings.edit().putString("apparent_power", df.format( appp )).apply();
            cur_settings.edit().putString("watt_hours",     df.format( wthr )).apply();
            cur_settings.edit().putString("power_factor",   df.format( pwfr )).apply();
            cur_settings.edit().putLong  ("time",  System.currentTimeMillis()).apply();
        }

    }

}
