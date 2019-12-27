import React from 'react';
import PropTypes from 'prop-types';
import { Card, Empty, List, Popconfirm, notification } from 'antd';
import axios from 'axios';
import Button from './Button';
import Grid from './Grid';

class ClientCard extends React.Component {
  state = {
    isDeleting: false,
    isFetchingPendingEmails: false,
    numPendingEmails: null,
    isFetchingNumberOfUsers: false,
    numUsers: null,
  };

  _onClickDelete = async () => {
    const { domain, onDelete } = this.props;
    const { isDeleting } = this.state;

    if (isDeleting) {
      return;
    }

    this.setState({ isDeleting: true });
    await onDelete(domain);
    this.setState({ isDeleting: false });
  };

  _onClickFetchPendingEmails = async () => {
    const { domain, fetchNumPendingEmails } = this.props;
    const { isFetchingPendingEmails } = this.state;

    if (isFetchingPendingEmails) {
      return;
    }

    this.setState({ isFetchingPendingEmails: true });
    const numPendingEmails = await fetchNumPendingEmails(domain);
    this.setState({ isFetchingPendingEmails: false, numPendingEmails });
  };

  _onClickFetchNumberOfUsers = async () => {
    const { domain, fetchNumUsers } = this.props;
    const { isFetchingNumberOfUsers } = this.state;

    if (isFetchingNumberOfUsers) {
      return;
    }

    this.setState({ isFetchingNumberOfUsers: true });
    const numUsers = await fetchNumUsers(domain);
    this.setState({ isFetchingNumberOfUsers: false, numUsers });
  };

  render() {
    const { domain } = this.props;

    const {
      isDeleting,
      isFetchingPendingEmails,
      numPendingEmails,
      isFetchingNumberOfUsers,
      numUsers,
    } = this.state;

    return (
      <Card
        actions={[
          <Popconfirm
            title={
              <span>
                This will delete client <em>{domain}</em>.
                <br />
                Are you sure?
              </span>
            }
            cancelText="No, cancel."
            okText="Yes, delete!"
            onConfirm={this._onClickDelete}
            disabled={isDeleting}
          >
            <Button icon={isDeleting ? 'loading' : 'delete'} />
          </Popconfirm>,
          <div>
            <Button
              icon={isFetchingPendingEmails ? 'loading' : 'mail'}
              onClick={this._onClickFetchPendingEmails}
            />
            {this.state.numPendingEmails != null && (
              <span>&nbsp;{numPendingEmails}</span>
            )}
          </div>,
          <div>
            <Button
              icon={isFetchingNumberOfUsers ? 'loading' : 'user'}
              onClick={this._onClickFetchNumberOfUsers}
            />
            {this.state.numUsers != null && <span>&nbsp;{numUsers}</span>}
          </div>,
        ]}
        style={{
          textDecoration: isDeleting ? 'line-through' : undefined,
        }}
      >
        {domain}
      </Card>
    );
  }
}

ClientCard.propTypes = {
  domain: PropTypes.string.isRequired,
  fetchNumPendingEmails: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

class ClientStats extends React.Component {
  state = {
    clients: [],
    isLoading: true,
  };

  get _client() {
    const {
      serverEndpoint,
      githubUsername,
      githubAccessToken,
    } = this.props.settings;

    return axios.create({
      baseURL: serverEndpoint,
      auth: {
        username: githubUsername,
        password: githubAccessToken,
      },
    });
  }

  get _isEnabled() {
    const { githubUsername, githubAccessToken } = this.props.settings;

    return githubUsername && githubAccessToken;
  }

  _fetchClients = async () => {
    let { clients } = this.state;

    try {
      const response = await this._client.get('/api/email/register/');
      clients = response.data.clients.sort();
    } catch (e) {
      notification.error({
        message: 'Unable to fetch clients',
        description: (e.response && e.response.data) || e.message,
      });
    }

    this.setState({
      clients,
      isLoading: false,
    });
  };

  _deleteClient = async domain => {
    try {
      await this._client
        .delete(`/api/email/register/${domain}`)
        .then(this._fetchClients);
    } catch (e) {
      notification.error({
        message: `Unable to delete client ${domain}`,
        description: (e.response && e.response.data) || e.message,
      });
    }
  };

  _fetchNumPendingEmails = async domain => {
    try {
      const response = await this._client.get(
        `/api/email/metrics/pending/${domain}`
      );
      return response.data.pending_emails;
    } catch (e) {
      notification.error({
        message: `Unable to fetch pending emails for client ${domain}`,
        description: (e.response && e.response.data) || e.message,
      });
      return null;
    }
  };

  _fetchNumUsers = async domain => {
    try {
      const response = await this._client.get(
        `/api/email/metrics/users/${domain}`
      );
      return response.data.users;
    } catch (e) {
      notification.error({
        message: `Unable to fetch number of users for client ${domain}`,
        description: (e.response && e.response.data) || e.message,
      });
      return null;
    }
  };

  _renderListItem = ({ domain }) => {
    return (
      <List.Item key={domain}>
        <ClientCard
          domain={domain}
          onDelete={this._deleteClient}
          fetchNumPendingEmails={this._fetchNumPendingEmails}
          fetchNumUsers={this._fetchNumUsers}
        />
      </List.Item>
    );
  };

  componentDidMount() {
    if (this._isEnabled) {
      this._fetchClients();
    }
  }

  render() {
    const { isLoading, clients } = this.state;

    if (!this._isEnabled) {
      return (
        <Empty description="Add Github access token in settings to view clients." />
      );
    }

    return (
      <Grid
        loading={isLoading}
        dataSource={clients}
        renderItem={this._renderListItem}
      />
    );
  }
}

ClientStats.propTypes = {
  settings: PropTypes.shape({
    githubAccessToken: PropTypes.string,
    githubUsername: PropTypes.string,
    serverEndpoint: PropTypes.string.isRequired,
  }).isRequired,
};

export default ClientStats;
