package edu.umich.eecs.lab11.powerblade;

import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.drawable.ColorDrawable;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.support.v7.app.ActionBarActivity;
import android.widget.TextView;

import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Date;

public class DetailActivity extends ActionBarActivity implements SharedPreferences.OnSharedPreferenceChangeListener {

    private Intent bleIntent;
    private String mDeviceName;
    private String mDevicePower;
    private String mDeviceAddress;
    private SharedPreferences cur_settings;
    private DateFormat format = new SimpleDateFormat("h:mm:ss a");
    public static final String EXTRAS_DEVICE_NAME = "DEVICE_NAME";
    public static final String EXTRAS_DEVICE_POWER = "DEVICE_POWER";
    public static final String EXTRAS_DEVICE_ADDRESS = "DEVICE_ADDRESS";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_detail);
        mDeviceName = getIntent().getStringExtra(EXTRAS_DEVICE_NAME);
        mDevicePower = getIntent().getStringExtra(EXTRAS_DEVICE_POWER);
        mDeviceAddress = getIntent().getStringExtra(EXTRAS_DEVICE_ADDRESS);
        cur_settings = PreferenceManager.getDefaultSharedPreferences(this);
        getSupportActionBar().setBackgroundDrawable(new ColorDrawable(0xff00274c));
        getSupportActionBar().setTitle("  PowerBlade #" + mDeviceName + "  ");
        getSupportActionBar().setDisplayShowHomeEnabled(true);
        getSupportActionBar().setLogo(R.drawable.ic_launcher);
        getSupportActionBar().setDisplayUseLogoEnabled(true);
        ((TextView) findViewById(R.id.row2)).setText(mDeviceName);
        ((TextView) findViewById(R.id.powr)).setText(mDevicePower + "W");
        ((TextView) findViewById(R.id.addr)).setText("DEVICE: " + mDeviceAddress);
    }

    @Override
    protected void onResume() {
        super.onResume();
        bleIntent = new Intent(this,BleService.class);
        cur_settings.registerOnSharedPreferenceChangeListener(this);
        this.startService(bleIntent);
        updateValues();
    }

    @Override
    protected void onPause() {
        super.onPause();
        this.stopService(bleIntent);
        cur_settings.unregisterOnSharedPreferenceChangeListener(this);
    }

    @Override
    public void onSharedPreferenceChanged(SharedPreferences sharedPreferences, String key) {
        updateValues();
    }

    public void updateValues() {
        if(mDeviceAddress.equals(cur_settings.getString("address","?"))) {
            ((TextView) findViewById(R.id.powr)).setText(cur_settings.getString("power", "?") + "W");
            ((TextView) findViewById(R.id.row5)).setText(cur_settings.getString("v_rms", "?") + " V");
            ((TextView) findViewById(R.id.row6)).setText(cur_settings.getString("true_power", "?") + " W");
            ((TextView) findViewById(R.id.row7)).setText(cur_settings.getString("apparent_power", "?") + " W");
            ((TextView) findViewById(R.id.row8)).setText(cur_settings.getString("watt_hours", "?") + " Wh");
            ((TextView) findViewById(R.id.row9)).setText(cur_settings.getString("power_factor", "?"));
            ((TextView) findViewById(R.id.time)).setText("RECEIVED: " + format.format(new Date(cur_settings.getLong("time",0))));
        }
    }

}
