package edu.umich.eecs.lab11.powerblade;

import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.drawable.ColorDrawable;
import android.os.Bundle;
import android.preference.PreferenceManager;
import android.support.v4.app.ListFragment;
import android.support.v7.app.ActionBarActivity;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.ListView;
import android.widget.TextView;

import java.util.HashMap;
import java.util.Map;

public class ListingActivity extends ActionBarActivity {

    private Intent bleIntent;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getSupportActionBar().setDisplayUseLogoEnabled(true);
        getSupportActionBar().setDisplayShowHomeEnabled(true);
        getSupportActionBar().setLogo(R.drawable.ic_launcher);
        getSupportActionBar().setBackgroundDrawable(new ColorDrawable(0xff00274c));
        getSupportFragmentManager().beginTransaction().replace(android.R.id.content,new ListingFragment()).commit();
    }

    @Override
    protected void onResume() {
        super.onResume();
        bleIntent = new Intent(this,BleService.class);
        this.startService(bleIntent);
    }

    @Override
    protected void onPause() {
        super.onPause();
        this.stopService(bleIntent);
    }

    public static class ListingFragment extends ListFragment implements SharedPreferences.OnSharedPreferenceChangeListener {

        private SharedPreferences cur_settings;
        private LeDeviceListAdapter mLeDeviceListAdapter;

        @Override
        public void onActivityCreated(Bundle savedInstanceState) {
            super.onActivityCreated(savedInstanceState);
            cur_settings = PreferenceManager.getDefaultSharedPreferences(getActivity());
        }

        @Override
        public void onResume() {
            super.onResume();
            mLeDeviceListAdapter = new LeDeviceListAdapter();
            cur_settings.registerOnSharedPreferenceChangeListener(this);
            setListAdapter(mLeDeviceListAdapter);
            setListShown(false);
        }

        @Override
        public void onPause() {
            super.onPause();
            cur_settings.unregisterOnSharedPreferenceChangeListener(this);
            mLeDeviceListAdapter.clear();
        }

        @Override
        public void onListItemClick(ListView listView, View view, int position, long id) {
            Map<String,String> device = mLeDeviceListAdapter.getDevice(position);
            if (device == null) return;
            Intent intent = new Intent(this.getActivity(), DetailActivity.class);
            intent.putExtra(DetailActivity.EXTRAS_DEVICE_NAME, device.get("id"));
            intent.putExtra(DetailActivity.EXTRAS_DEVICE_POWER, device.get("power"));
            intent.putExtra(DetailActivity.EXTRAS_DEVICE_ADDRESS, device.get("address"));
            mLeDeviceListAdapter.clear();
            startActivity(intent);
        }

        @Override
        public void onSharedPreferenceChanged(SharedPreferences sharedPreferences, String key) {
            mLeDeviceListAdapter.addDevice(cur_settings.getString("address", "?"), cur_settings.getString("id", "?"),cur_settings.getString("power","?"));
            mLeDeviceListAdapter.notifyDataSetChanged();
            setListShown(true);
        }

        private class LeDeviceListAdapter extends BaseAdapter {

            private LayoutInflater mInflator;
            private Map<String,Map<String,String>> mLeDevices;

            public LeDeviceListAdapter() {
                super();
                mLeDevices = new HashMap<>();
                mInflator = getActivity().getLayoutInflater();
            }

            public void addDevice(String address, String id, String power) {
                if(address!="?") {
                    Map<String,String> device = new HashMap<>();
                    device.put("id",id);
                    device.put("power",power);
                    device.put("address",address);
                    mLeDevices.put(address,device);
                }
            }

            public Map<String,String> getDevice(int position) { return mLeDevices.get(mLeDevices.keySet().toArray()[position]); }

            public void clear() {
                mLeDevices.clear();
            }

            @Override
            public int getCount() {
                return mLeDevices.size();
            }

            @Override
            public Object getItem(int i) {
                return mLeDevices.get(i);
            }

            @Override
            public long getItemId(int i) {
                return i;
            }

            @Override
            public View getView(int i, View view, ViewGroup viewGroup) {
                ViewHolder viewHolder;
                if (view == null) {
                    view = mInflator.inflate(R.layout.listitem_device, null);
                    viewHolder = new ViewHolder();
                    viewHolder.deviceAddress = (TextView) view.findViewById(R.id.device_address);
                    viewHolder.deviceName = (TextView) view.findViewById(R.id.device_name);
                    viewHolder.devicePower = (TextView) view.findViewById(R.id.device_power);
                    view.setTag(viewHolder);
                } else viewHolder = (ViewHolder) view.getTag();
                Map<String,String> device = getDevice(i);
                viewHolder.deviceAddress.setText(device.get("address"));
                viewHolder.deviceName.setText("PowerBlade #" + device.get("id"));
                viewHolder.devicePower.setText(device.get("power") + "W");
                return view;
            }

        }

    }

    public static class ViewHolder {
        TextView deviceName;
        TextView devicePower;
        TextView deviceAddress;
    }

}
