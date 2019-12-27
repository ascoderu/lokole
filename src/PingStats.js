import React from 'react';
import PropTypes from 'prop-types';
import { Card, Icon, List, Statistic, notification } from 'antd';
import axios from 'axios';
import Grid from './Grid';

const colors = {
  success: '#3f8600',
  failure: '#cf1322',
};

class PingStats extends React.Component {
  state = {
    pingTimeMillis: undefined,
    pingSuccess: undefined,
  };

  _pingInterval = undefined;

  _onPing = async () => {
    const { serverEndpoint } = this.props.settings;

    const pingStart = new Date().getTime();

    let pingSuccess;
    try {
      await axios.get(`${serverEndpoint}/healthcheck/ping`);
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

  _renderListItem = props => {
    return (
      <List.Item key={props.title}>
        <Card>
          <Statistic {...props} />
        </Card>
      </List.Item>
    );
  };

  get _isLoading() {
    const { pingTimeMillis, pingSuccess } = this.state;

    return pingTimeMillis == null || pingSuccess == null;
  }

  get _stats() {
    const { pingTimeMillis, pingSuccess } = this.state;

    if (this._isLoading) {
      return [];
    }

    return [
      {
        title: 'Server ping',
        value: pingTimeMillis,
        suffix: 'ms',
        prefix: <Icon type={pingSuccess ? 'check' : 'warning'} />,
        valueStyle: {
          color: pingSuccess ? colors.success : colors.failure,
        },
      },
    ];
  }

  async componentDidMount() {
    const { pingIntervalSeconds } = this.props.settings;

    await this._onPing();

    this._pingInterval = setInterval(this._onPing, pingIntervalSeconds * 1000);
  }

  componentWillUnmount() {
    if (this._pingInterval != null) {
      clearInterval(this._pingInterval);
    }
  }

  render() {
    return (
      <Grid
        loading={this._isLoading}
        dataSource={this._stats}
        renderItem={this._renderListItem}
      />
    );
  }
}

PingStats.propTypes = {
  settings: PropTypes.shape({
    pingIntervalSeconds: PropTypes.number.isRequired,
    serverEndpoint: PropTypes.string.isRequired,
  }).isRequired,
};

export default PingStats;
