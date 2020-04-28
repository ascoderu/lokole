import React from 'react';
import PropTypes from 'prop-types';
import { Card, Icon, List, Statistic, notification } from 'antd';
import axios from 'axios';
import Grid from './Grid';

const colors = {
  success: '#3f8600',
  failure: '#cf1322',
};

class PingStat extends React.Component {
  state = {
    pingTimeMillis: undefined,
    pingSuccess: undefined,
  };

  _pingInterval = undefined;

  _onPing = async () => {
    const { serverEndpoint } = this.props;

    const pingStart = new Date().getTime();

    let pingSuccess;
    try {
      await axios.get(serverEndpoint);
      pingSuccess = true;
    } catch (e) {
      notification.error({
        message: 'Unable to ping server',
        description: (e.response && e.response.data) || e.message,
      });
      pingSuccess = false;
    }

    this.setState({
      pingTimeMillis: new Date().getTime() - pingStart,
      pingSuccess,
    });
  };

  async componentDidMount() {
    const { pingIntervalSeconds } = this.props;

    await this._onPing();

    this._pingInterval = setInterval(this._onPing, pingIntervalSeconds * 1000);
  }

  componentWillUnmount() {
    if (this._pingInterval != null) {
      clearInterval(this._pingInterval);
    }
  }

  render() {
    const { title } = this.props;
    const { pingSuccess, pingTimeMillis } = this.state;

    return (
      <List.Item key={title}>
        <Card>
          <Statistic
            title={title}
            value={pingTimeMillis}
            suffix="ms"
            prefix={<Icon type={pingSuccess ? 'check' : 'warning'} />}
            valueStyle={{
              color: pingSuccess ? colors.success : colors.failure,
            }}
          />
        </Card>
      </List.Item>
    );
  }
}

PingStat.propTypes = {
  title: PropTypes.string.isRequired,
  serverEndpoint: PropTypes.string.isRequired,
  pingIntervalSeconds: PropTypes.number.isRequired,
};

function PingStats(props) {
  const { serverEndpoint, pingIntervalSeconds } = props.settings;

  return (
    <Grid>
      <PingStat
        title="Server ping"
        pingIntervalSeconds={pingIntervalSeconds}
        serverEndpoint={`${serverEndpoint}/healthcheck/ping`}
      />
      <PingStat
        title="Webapp ping"
        pingIntervalSeconds={pingIntervalSeconds}
        serverEndpoint={`${serverEndpoint}/web/healthcheck/ping`}
      />
    </Grid>
  );
}

PingStats.propTypes = {
  settings: PropTypes.shape({
    pingIntervalSeconds: PropTypes.number.isRequired,
    serverEndpoint: PropTypes.string.isRequired,
  }).isRequired,
};

export default PingStats;
